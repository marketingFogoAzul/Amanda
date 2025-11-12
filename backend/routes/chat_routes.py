from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Chat, MensagemChat, Empresa, Relatorio, LogAuditoria
from config import Config
from services.ai_service import NegociadorAmanda
from services.moderation_service import ModeradorConteudo
from utils.validators import Validadores
from datetime import datetime, timedelta
import re

chat_bp = Blueprint('chat', __name__)

# 🧠 Instâncias de serviços
negociador = NegociadorAmanda()
moderador = ModeradorConteudo()

# 💼 Chats ativos com humanos
active_human_chats = {}

@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """
    Envia mensagem no chat - endpoint principal da Amanda AI
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    message = data.get('message', '').strip()
    chat_id = data.get('chat_id')
    tipo_mensagem = data.get('tipo', 'texto')  # texto, acao, sistema

    # 🛡️ Validação da mensagem
    valid_msg, msg_erro = Validadores.validar_mensagem_chat(message)
    if not valid_msg:
        return jsonify({'error': msg_erro}), 400

    try:
        # 🔍 Verificação de conteúdo proibido
        violacao = moderador.verificar_conteudo_proibido(message)
        if violacao:
            return handle_content_violation(chat_id, message, violacao, current_user.id)

        # 💬 Criar ou recuperar chat
        chat = get_or_create_chat(chat_id, message, current_user.id)
        
        # 💾 Salvar mensagem do usuário
        mensagem_usuario = MensagemChat(
            chat_id=chat.id,
            tipo_remetente='usuario',
            conteudo=message
        )
        db.session.add(mensagem_usuario)
        db.session.flush()  # Para obter ID
        
        # 📝 Log da mensagem do usuário
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='mensagem_enviada',
            modulo='chat',
            tipo_recurso='mensagem',
            recurso_id=mensagem_usuario.id,
            detalhes=f'Chat {chat.id}: Mensagem do usuário enviada',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)

        # 👥 Verificar se chat está com humano
        if chat.id in active_human_chats:
            db.session.commit()
            
            # 📝 Log de mensagem para humano
            log_auditoria = LogAuditoria(
                usuario_id=current_user.id,
                acao='mensagem_encaminhada',
                modulo='chat',
                tipo_recurso='chat',
                recurso_id=chat.id,
                detalhes=f'Chat {chat.id}: Mensagem encaminhada para atendente humano',
                status='sucesso',
                endereco_ip=request.remote_addr,
                agente_usuario=request.user_agent.string
            )
            db.session.add(log_auditoria)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'chat_id': chat.id,
                'human_handling': True,
                'message': 'Mensagem enviada para representante humano'
            })
        
        # 🤖 Gerar resposta da Amanda
        historico = get_chat_history(chat.id)
        resposta_amanda = negociador.gerar_resposta_negociacao(message, historico)
        
        # 💾 Salvar resposta da Amanda
        mensagem_amanda = MensagemChat(
            chat_id=chat.id,
            tipo_remetente='amanda',
            conteudo=resposta_amanda['conteudo']
        )
        db.session.add(mensagem_amanda)
        db.session.flush()
        
        # 📝 Log da resposta da Amanda
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='resposta_amanda_gerada',
            modulo='chat',
            tipo_recurso='mensagem',
            recurso_id=mensagem_amanda.id,
            detalhes=f'Chat {chat.id}: Resposta da Amanda gerada com sucesso',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'chat_id': chat.id,
            'amanda_response': resposta_amanda['conteudo'],
            'actions': resposta_amanda.get('acoes', []),
            'summary': resposta_amanda.get('resumo', ''),
            'timestamp': Config.get_current_timestamp(),
            'message_id': mensagem_amanda.id
        })
        
    except Exception as e:
        print(f'❌ Erro ao enviar mensagem: {e}')
        db.session.rollback()
        
        # 📝 Log de erro
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='mensagem_erro',
            modulo='chat',
            tipo_recurso='chat',
            recurso_id=chat_id,
            detalhes=f'Erro ao enviar mensagem: {str(e)}',
            status='erro',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({'error': 'Erro interno do servidor'}), 500

@chat_bp.route('/history', methods=['GET'])
@login_required
def get_chat_history_route():
    """
    Obtém histórico de chats do usuário
    """
    try:
        chat_id = request.args.get('chat_id')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if chat_id:
            # 📜 Histórico de um chat específico
            return get_specific_chat_history(chat_id, current_user.id, limit, offset)
        else:
            # 📋 Lista de todos os chats do usuário
            chats = Chat.query.filter_by(usuario_id=current_user.id)\
                             .order_by(Chat.atualizado_em.desc())\
                             .offset(offset)\
                             .limit(limit)\
                             .all()
            
            chats_data = []
            for chat in chats:
                ultima_msg = chat.ultima_mensagem()
                chats_data.append({
                    'id': chat.id,
                    'titulo': chat.titulo,
                    'status': chat.status,
                    'criado_em': chat.criado_em,
                    'atualizado_em': chat.atualizado_em,
                    'quantidade_mensagens': chat.quantidade_mensagens(),
                    'ultima_mensagem': ultima_msg.conteudo if ultima_msg else '',
                    'ultima_mensagem_tipo': ultima_msg.tipo_remetente if ultima_msg else '',
                    'ultima_mensagem_timestamp': ultima_msg.timestamp if ultima_msg else '',
                    'esta_assumido': chat.esta_assumido(),
                    'esta_fechado': chat.esta_fechado(),
                    'foi_avaliado': chat.foi_avaliado()
                })
            
            # 📊 Estatísticas
            total_chats = Chat.query.filter_by(usuario_id=current_user.id).count()
            chats_ativos = Chat.query.filter_by(usuario_id=current_user.id, status='ativo').count()
            chats_fechados = Chat.query.filter_by(usuario_id=current_user.id, status='fechado').count()
            
            return jsonify({
                'success': True,
                'chats': chats_data,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total': total_chats
                },
                'stats': {
                    'total': total_chats,
                    'ativos': chats_ativos,
                    'fechados': chats_fechados
                }
            })
            
    except Exception as e:
        print(f'❌ Erro ao obter histórico: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@chat_bp.route('/create', methods=['POST'])
@login_required
def create_chat():
    """
    Cria um novo chat
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    titulo = data.get('titulo', 'Nova Negociação').strip()
    empresa_id = data.get('empresa_id')

    try:
        # 🏢 Verificar se empresa pertence ao usuário (se for usuário empresarial)
        if empresa_id and current_user.eh_usuario_empresa():
            empresa = Empresa.query.get(empresa_id)
            if not empresa or empresa.id != current_user.empresa_id:
                return jsonify({'error': 'Empresa não encontrada ou não autorizada'}), 403
        
        # 💬 Criar novo chat
        novo_chat = Chat(
            usuario_id=current_user.id,
            empresa_id=empresa_id if current_user.eh_usuario_empresa() else None,
            titulo=titulo,
            status='ativo'
        )
        db.session.add(novo_chat)
        db.session.flush()
        
        # 👋 Mensagem de boas-vindas da Amanda
        mensagem_amanda = MensagemChat(
            chat_id=novo_chat.id,
            tipo_remetente='amanda',
            conteudo='Olá! Sou a Amanda AI, sua assistente de negociação. Como posso ajudá-lo hoje?'
        )
        db.session.add(mensagem_amanda)
        
        # 📝 Log de criação do chat
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='chat_criado',
            modulo='chat',
            tipo_recurso='chat',
            recurso_id=novo_chat.id,
            detalhes=f'Novo chat criado: {titulo}',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'chat': novo_chat.to_dict(),
            'message': 'Chat criado com sucesso'
        })
        
    except Exception as e:
        print(f'❌ Erro ao criar chat: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@chat_bp.route('/<int:chat_id>/close', methods=['POST'])
@login_required
def close_chat(chat_id):
    """
    Fecha um chat
    """
    try:
        chat = Chat.query.get(chat_id)
        
        if not chat:
            return jsonify({'error': 'Chat não encontrado'}), 404
        
        # 🔒 Verificar permissão
        if chat.usuario_id != current_user.id and not current_user.eh_admin():
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        if chat.esta_fechado():
            return jsonify({'error': 'Chat já está fechado'}), 400
        
        # 🔒 Fechar chat
        chat.fechar_chat()
        
        # 📝 Log de fechamento
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='chat_fechado',
            modulo='chat',
            tipo_recurso='chat',
            recurso_id=chat_id,
            detalhes='Chat fechado pelo usuário',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat fechado com sucesso'
        })
        
    except Exception as e:
        print(f'❌ Erro ao fechar chat: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@chat_bp.route('/<int:chat_id>/evaluate', methods=['POST'])
@login_required
def evaluate_chat(chat_id):
    """
    Avalia um chat finalizado
    """
    from models import Avaliacao
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    rating = data.get('rating')
    comment = data.get('comment', '').strip()
    
    # 🏷️ Categorias de avaliação
    categories = data.get('categories', {})
    
    # 🛡️ Validações
    if rating is None:
        return jsonify({'error': 'Avaliação é obrigatória'}), 400
    
    if not Validadores.validar_avaliacao(rating):
        return jsonify({'error': 'Avaliação deve ser entre 1 e 5'}), 400
    
    try:
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({'error': 'Chat não encontrado'}), 404
        
        # 🔒 Verificar se o usuário é participante do chat
        if chat.usuario_id != current_user.id:
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        # 🔒 Verificar se chat está fechado
        if not chat.esta_fechado():
            return jsonify({'error': 'Apenas chats finalizados podem ser avaliados'}), 400
        
        # 🔒 Verificar se já foi avaliado
        if chat.foi_avaliado():
            return jsonify({'error': 'Este chat já foi avaliado'}), 400
        
        # ⭐ Criar avaliação
        avaliacao = Avaliacao(
            chat_id=chat_id,
            nota=rating,
            comentario=comment,
            atendimento_rapido=categories.get('atendimento_rapido', False),
            proposta_justa=categories.get('proposta_justa', False),
            comunicacao_clara=categories.get('comunicacao_clara', False),
            resolucao_eficaz=categories.get('resolucao_eficaz', False)
        )
        db.session.add(avaliacao)
        
        # 📝 Log de avaliação
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='avaliacao_registrada',
            modulo='chat',
            tipo_recurso='chat',
            recurso_id=chat_id,
            detalhes=f'Avaliação registrada: {rating} estrelas',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Avaliação registrada com sucesso',
            'evaluation': avaliacao.to_dict()
        })
        
    except Exception as e:
        print(f'❌ Erro ao avaliar chat: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@chat_bp.route('/stats', methods=['GET'])
@login_required
def get_chat_stats():
    """
    Obtém estatísticas dos chats do usuário
    """
    try:
        # 📊 Estatísticas gerais
        total_chats = Chat.query.filter_by(usuario_id=current_user.id).count()
        chats_ativos = Chat.query.filter_by(usuario_id=current_user.id, status='ativo').count()
        chats_fechados = Chat.query.filter_by(usuario_id=current_user.id, status='fechado').count()
        chats_assumidos = Chat.query.filter_by(usuario_id=current_user.id, status='assumido').count()
        
        # 📈 Mensagens totais
        total_mensagens = db.session.query(MensagemChat).join(Chat).filter(
            Chat.usuario_id == current_user.id
        ).count()
        
        # ⭐ Avaliações (se for usuário empresarial)
        avaliacoes_data = {}
        if current_user.eh_usuario_empresa():
            from models import Avaliacao
            avaliacoes = db.session.query(Avaliacao).join(Chat).filter(
                Chat.empresa_id == current_user.empresa_id
            ).all()
            
            if avaliacoes:
                media_avaliacao = sum(av.nota for av in avaliacoes) / len(avaliacoes)
                distribuicao = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for av in avaliacoes:
                    if 1 <= av.nota <= 5:
                        distribuicao[av.nota] += 1
                
                avaliacoes_data = {
                    'total': len(avaliacoes),
                    'media': round(media_avaliacao, 1),
                    'distribuicao': distribuicao
                }
        
        return jsonify({
            'success': True,
            'stats': {
                'chats': {
                    'total': total_chats,
                    'ativos': chats_ativos,
                    'fechados': chats_fechados,
                    'assumidos': chats_assumidos
                },
                'mensagens': {
                    'total': total_mensagens
                },
                'avaliacoes': avaliacoes_data
            }
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter estatísticas: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

# 🔧 Funções auxiliares
def get_or_create_chat(chat_id, message, user_id):
    """Obtém ou cria um chat"""
    if chat_id:
        chat = Chat.query.get(chat_id)
        if chat and chat.usuario_id == user_id and not chat.esta_fechado():
            # 🔄 Atualizar timestamp
            chat.atualizado_em = Config.get_current_timestamp()
            return chat
    
    # 💬 Criar novo chat
    titulo = message[:50] + '...' if len(message) > 50 else message
    novo_chat = Chat(
        usuario_id=user_id,
        titulo=titulo,
        status='ativo'
    )
    db.session.add(novo_chat)
    db.session.flush()
    
    return novo_chat

def get_chat_history(chat_id):
    """Obtém histórico do chat"""
    mensagens = MensagemChat.query.filter_by(chat_id=chat_id)\
                                 .order_by(MensagemChat.timestamp)\
                                 .all()
    
    historico = []
    for msg in mensagens:
        historico.append({
            'tipo_remetente': msg.tipo_remetente,
            'conteudo': msg.conteudo,
            'timestamp': msg.timestamp,
            'removida': msg.removida
        })
    
    return historico

def get_specific_chat_history(chat_id, user_id, limit=50, offset=0):
    """Obtém histórico de um chat específico"""
    chat = Chat.query.get(chat_id)
    
    if not chat or chat.usuario_id != user_id:
        return jsonify({'error': 'Chat não encontrado'}), 404
    
    # 📜 Buscar mensagens com paginação
    mensagens = MensagemChat.query.filter_by(chat_id=chat_id)\
                                 .order_by(MensagemChat.timestamp.desc())\
                                 .offset(offset)\
                                 .limit(limit)\
                                 .all()
    
    # 🔄 Ordenar por timestamp crescente para exibição
    mensagens_ordenadas = sorted(mensagens, key=lambda x: x.timestamp)
    
    mensagens_data = []
    for msg in mensagens_ordenadas:
        mensagens_data.append(msg.to_dict())
    
    return jsonify({
        'success': True,
        'chat': chat.to_dict(),
        'messages': mensagens_data,
        'pagination': {
            'limit': limit,
            'offset': offset,
            'total': chat.quantidade_mensagens()
        }
    })

def handle_content_violation(chat_id, message, violation_type, user_id):
    """Lida com violação de conteúdo proibido"""
    try:
        # 💬 Criar chat se não existir
        if not chat_id:
            chat = Chat(
                usuario_id=user_id,
                titulo='Chat com violação de regras',
                status='reportado'
            )
            db.session.add(chat)
            db.session.flush()
            chat_id = chat.id
        else:
            chat = Chat.query.get(chat_id)
            chat.status = 'reportado'
        
        # 🚫 Mensagem redigida do usuário
        mensagem_usuario = MensagemChat(
            chat_id=chat_id,
            tipo_remetente='usuario',
            conteudo='[MENSAGEM COM INFORMAÇÕES DE CONTATO REMOVIDA]',
            removida=True,
            motivo_remocao=f'Detectado {violation_type}'
        )
        db.session.add(mensagem_usuario)
        
        # 📋 Criar relatório automático
        relatorio = Relatorio(
            relator_id=user_id,
            chat_id=chat_id,
            motivo=f'Informações de contato detectadas: {violation_type}',
            categoria='contato',
            status='resolvido'
        )
        db.session.add(relatorio)
        
        # ⏳ Congelar usuário por 3 dias
        from models import Usuario
        usuario = Usuario.query.get(user_id)
        congelado_ate = (datetime.now() + timedelta(days=3)).strftime('%d/%m/%Y %H:%M:%S')
        usuario.congelado_ate = congelado_ate
        
        # 💬 Mensagem do sistema
        mensagem_sistema = MensagemChat(
            chat_id=chat_id,
            tipo_remetente='sistema',
            conteudo=f'Possível violação das regras detectada - conta suspensa até {congelado_ate}.'
        )
        db.session.add(mensagem_sistema)
        
        # 📝 Log da violação
        log_auditoria = LogAuditoria(
            usuario_id=user_id,
            acao='violacao_detectada',
            modulo='chat',
            tipo_recurso='chat',
            recurso_id=chat_id,
            detalhes=f'Violacao de conteudo: {violation_type}. Usuario congelado ate {congelado_ate}',
            status='aviso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        
        db.session.commit()
        
        return jsonify({
            'success': False,
            'error': 'Violação de regras detectada',
            'chat_closed': True,
            'freeze_until': congelado_ate
        })
        
    except Exception as e:
        print(f'❌ Erro ao lidar com violação: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

print("✅ Chat routes carregadas com sucesso!")