from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Empresa, Usuario, Chat, Avaliacao, AvisoEmpresa, LogAuditoria
from config import Config
from utils.validators import Validadores
from datetime import datetime, timedelta

company_bp = Blueprint('company', __name__)

@company_bp.route('/panel', methods=['GET'])
@login_required
def get_company_panel():
    """
    Obtém dados do painel da empresa para representantes e vendedores
    """
    if not current_user.pode_gerenciar_empresa():
        return jsonify({'error': 'Acesso não autorizado ao painel da empresa'}), 403
    
    if not current_user.empresa_id:
        return jsonify({'error': 'Usuário não vinculado a uma empresa'}), 403
    
    try:
        empresa = Empresa.query.get(current_user.empresa_id)
        if not empresa:
            return jsonify({'error': 'Empresa não encontrada'}), 404
        
        # 📊 Estatísticas da empresa
        total_chats = Chat.query.filter_by(empresa_id=empresa.id).count()
        chats_fechados = Chat.query.filter_by(empresa_id=empresa.id, status='fechado').count()
        chats_ativos = Chat.query.filter_by(empresa_id=empresa.id, status='ativo').count()
        chats_assumidos = Chat.query.filter_by(empresa_id=empresa.id, status='assumido').count()
        
        # ⭐ Média de avaliações
        avaliacoes = Avaliacao.query.join(Chat).filter(Chat.empresa_id == empresa.id).all()
        media_avaliacao = sum(av.nota for av in avaliacoes) / len(avaliacoes) if avaliacoes else 0
        
        # 👥 Membros da equipe ativos
        membros_equipe = Usuario.query.filter_by(empresa_id=empresa.id, ativo=True).all()
        
        # 📞 Chamados disponíveis (chats ativos não assumidos)
        chamados_disponiveis = Chat.query.filter_by(
            empresa_id=empresa.id, 
            status='ativo',
            assumido_por_id=None
        ).order_by(Chat.criado_em.desc()).limit(20).all()
        
        # 👤 Meus chamados (chats assumidos pelo usuário atual)
        meus_chamados = Chat.query.filter_by(
            empresa_id=empresa.id,
            assumido_por_id=current_user.id,
            status='assumido'
        ).order_by(Chat.assumido_em.desc()).all()
        
        # 📢 Avisos da empresa ativos
        avisos = AvisoEmpresa.query.filter_by(
            empresa_id=empresa.id,
            ativo=True
        ).order_by(AvisoEmpresa.criado_em.desc()).limit(10).all()
        
        # 📈 Estatísticas de desempenho da equipe
        desempenho_equipe = []
        for membro in membros_equipe:
            if membro.eh_usuario_empresa():  # Apenas representantes e vendedores
                chats_membro = Chat.query.filter_by(
                    empresa_id=empresa.id,
                    assumido_por_id=membro.id
                ).all()
                
                avaliacoes_membro = Avaliacao.query.join(Chat).filter(
                    Chat.empresa_id == empresa.id,
                    Chat.assumido_por_id == membro.id
                ).all()
                
                media_membro = sum(av.nota for av in avaliacoes_membro) / len(avaliacoes_membro) if avaliacoes_membro else 0
                
                desempenho_equipe.append({
                    'id': membro.id,
                    'nome': membro.nome_completo,
                    'cargo': membro.get_nome_cargo(),
                    'chats_atendidos': len(chats_membro),
                    'avaliacao_media': round(media_membro, 1),
                    'total_avaliacoes': len(avaliacoes_membro),
                    'ultimo_login': membro.ultimo_login
                })
        
        # 📝 Log de acesso ao painel
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='painel_empresa_acessado',
            modulo='company',
            tipo_recurso='empresa',
            recurso_id=empresa.id,
            detalhes=f'Painel da empresa {empresa.nome_fantasia} acessado',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'company': empresa.to_dict(),
            'stats': {
                'total_chats': total_chats,
                'closed_chats': chats_fechados,
                'active_chats': chats_ativos,
                'claimed_chats': chats_assumidos,
                'avg_rating': round(media_avaliacao, 1),
                'team_members': len(membros_equipe),
                'available_calls': len(chamados_disponiveis),
                'my_calls': len(meus_chamados)
            },
            'available_calls': [chat.to_dict() for chat in chamados_disponiveis],
            'my_calls': [chat.to_dict() for chat in meus_chamados],
            'team_members': [membro.to_dict() for membro in membros_equipe],
            'team_performance': desempenho_equipe,
            'notices': [aviso.to_dict() for aviso in avisos],
            'evaluations': [avaliacao.to_dict() for avaliacao in avaliacoes[-10:]]  # Últimas 10
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter painel da empresa: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@company_bp.route('/add-member', methods=['POST'])
@login_required
def add_team_member():
    """
    Adiciona membro à equipe da empresa (apenas representantes)
    """
    if current_user.cargo != 4:  # Apenas Representantes
        return jsonify({'error': 'Apenas representantes podem adicionar membros'}), 403
    
    if not current_user.empresa_id:
        return jsonify({'error': 'Usuário não vinculado a uma empresa'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    email = data.get('email', '').strip().lower()
    cargo = data.get('cargo', 5)  # Padrão: Vendedor
    
    if not email:
        return jsonify({'error': 'E-mail é obrigatório'}), 400
    
    if not Validadores.validar_email(email):
        return jsonify({'error': 'E-mail inválido'}), 400
    
    # 🛡️ Validar cargo (apenas vendedor para representantes adicionarem)
    if cargo not in [5]:  # Apenas Vendedor
        return jsonify({'error': 'Cargo não permitido'}), 400
    
    try:
        # 🔍 Buscar usuário
        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # 🔒 Verificar se já está na empresa
        if usuario.empresa_id == current_user.empresa_id:
            return jsonify({'error': 'Usuário já faz parte da equipe'}), 400
        
        # 🔒 Verificar se usuário não está em outra empresa
        if usuario.empresa_id is not None:
            return jsonify({'error': 'Usuário já pertence a outra empresa'}), 400
        
        # 👥 Adicionar à empresa
        usuario.empresa_id = current_user.empresa_id
        usuario.cargo = cargo
        usuario.atualizado_em = Config.get_current_timestamp()
        
        # 📝 Log de adição de membro
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='membro_adicionado',
            modulo='company',
            tipo_recurso='usuario',
            recurso_id=usuario.id,
            detalhes=f'Usuário {usuario.nome_completo} adicionado à empresa como {Config.get_role_name(cargo)}',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usuário {usuario.nome_completo} adicionado à equipe com sucesso',
            'user': usuario.to_dict()
        })
        
    except Exception as e:
        print(f'❌ Erro ao adicionar membro: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@company_bp.route('/remove-member', methods=['POST'])
@login_required
def remove_team_member():
    """
    Remove membro da equipe (apenas representantes)
    """
    if current_user.cargo != 4:  # Apenas Representantes
        return jsonify({'error': 'Apenas representantes podem remover membros'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'ID do usuário é obrigatório'}), 400
    
    try:
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # 🔒 Verificar se pertence à mesma empresa
        if usuario.empresa_id != current_user.empresa_id:
            return jsonify({'error': 'Usuário não pertence à sua empresa'}), 403
        
        # 🚫 Não permite remover a si mesmo
        if usuario.id == current_user.id:
            return jsonify({'error': 'Não é possível remover a si mesmo'}), 400
        
        # 🔒 Não permite remover outros representantes
        if usuario.cargo == 4:  # Representante
            return jsonify({'error': 'Não é possível remover outros representantes'}), 400
        
        # 👋 Remover da empresa (volta para Cliente Básico)
        empresa_anterior = usuario.empresa_id
        usuario.empresa_id = None
        usuario.cargo = 7  # Cliente Básico
        usuario.atualizado_em = Config.get_current_timestamp()
        
        # 📝 Log de remoção de membro
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='membro_removido',
            modulo='company',
            tipo_recurso='usuario',
            recurso_id=usuario.id,
            detalhes=f'Usuário {usuario.nome_completo} removido da empresa {empresa_anterior}',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usuário {usuario.nome_completo} removido da equipe'
        })
        
    except Exception as e:
        print(f'❌ Erro ao remover membro: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@company_bp.route('/create-notice', methods=['POST'])
@login_required
def create_company_notice():
    """
    Cria aviso da empresa (apenas representantes)
    """
    if current_user.cargo != 4:  # Apenas Representantes
        return jsonify({'error': 'Apenas representantes podem criar avisos'}), 403
    
    if not current_user.empresa_id:
        return jsonify({'error': 'Usuário não vinculado a uma empresa'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    if not title or not content:
        return jsonify({'error': 'Título e conteúdo são obrigatórios'}), 400
    
    if len(title) > 255:
        return jsonify({'error': 'Título muito longo (máximo 255 caracteres)'}), 400
    
    try:
        aviso = AvisoEmpresa(
            empresa_id=current_user.empresa_id,
            titulo=title,
            conteudo=content,
            criado_por_id=current_user.id
        )
        db.session.add(aviso)
        db.session.flush()
        
        # 📝 Log de criação de aviso
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='aviso_criado',
            modulo='company',
            tipo_recurso='aviso',
            recurso_id=aviso.id,
            detalhes=f'Aviso criado: {title}',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Aviso criado com sucesso',
            'notice': aviso.to_dict()
        })
        
    except Exception as e:
        print(f'❌ Erro ao criar aviso: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@company_bp.route('/evaluations', methods=['GET'])
@login_required
def get_company_evaluations():
    """
    Obtém avaliações da empresa
    """
    if not current_user.pode_gerenciar_empresa():
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    if not current_user.empresa_id:
        return jsonify({'error': 'Usuário não vinculado a uma empresa'}), 403
    
    try:
        # ⏰ Filtro de tempo
        time_filter = request.args.get('time_filter', '30')
        
        # 📅 Calcula data de corte
        if time_filter == '7':
            cutoff_date = datetime.now() - timedelta(days=7)
        elif time_filter == '90':
            cutoff_date = datetime.now() - timedelta(days=90)
        else:  # 30 dias padrão
            cutoff_date = datetime.now() - timedelta(days=30)
        
        # Buscar avaliações da empresa
        avaliacoes = Avaliacao.query.join(Chat).filter(
            Chat.empresa_id == current_user.empresa_id
        ).order_by(Avaliacao.criado_em.desc()).all()
        
        # 📊 Estatísticas
        total_avaliacoes = len(avaliacoes)
        media_geral = sum(av.nota for av in avaliacoes) / total_avaliacoes if total_avaliacoes > 0 else 0
        
        # 📈 Distribuição das notas
        distribuicao = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for av in avaliacoes:
            if 1 <= av.nota <= 5:
                distribuicao[av.nota] += 1
        
        # 🏷️ Categorias mais selecionadas
        categorias = {
            'atendimento_rapido': sum(1 for av in avaliacoes if av.atendimento_rapido),
            'proposta_justa': sum(1 for av in avaliacoes if av.proposta_justa),
            'comunicacao_clara': sum(1 for av in avaliacoes if av.comunicacao_clara),
            'resolucao_eficaz': sum(1 for av in avaliacoes if av.resolucao_eficaz)
        }
        
        return jsonify({
            'success': True,
            'evaluations': [av.to_dict() for av in avaliacoes],
            'stats': {
                'total': total_avaliacoes,
                'average': round(media_geral, 1),
                'distribution': distribuicao,
                'categories': categorias
            }
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter avaliações: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@company_bp.route('/update-settings', methods=['PUT'])
@login_required
def update_company_settings():
    """
    Atualiza configurações da empresa (apenas representantes)
    """
    if current_user.cargo != 4:  # Apenas Representantes
        return jsonify({'error': 'Apenas representantes podem atualizar configurações'}), 403
    
    if not current_user.empresa_id:
        return jsonify({'error': 'Usuário não vinculado a uma empresa'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    try:
        empresa = Empresa.query.get(current_user.empresa_id)
        updated = False
        changes = []
        
        # 📞 Atualizar telefone
        if 'telefone' in data:
            telefone = data['telefone'].strip()
            if telefone and not Validadores.validar_telefone(telefone):
                return jsonify({'error': 'Telefone inválido'}), 400
            
            if telefone != empresa.telefone:
                changes.append(f'Telefone: {empresa.telefone} → {telefone}')
                empresa.telefone = telefone
                updated = True
        
        # 📧 Atualizar email
        if 'email' in data:
            email = data['email'].strip().lower()
            if email and not Validadores.validar_email(email):
                return jsonify({'error': 'E-mail inválido'}), 400
            
            if email != empresa.email:
                changes.append(f'E-mail: {empresa.email} → {email}')
                empresa.email = email
                updated = True
        
        # 📍 Atualizar endereço
        if 'endereco' in data:
            endereco = data['endereco'].strip()
            valid_endereco, msg_endereco = Validadores.validar_endereco(endereco)
            if not valid_endereco:
                return jsonify({'error': msg_endereco}), 400
            
            if endereco != empresa.endereco:
                changes.append('Endereço atualizado')
                empresa.endereco = endereco
                updated = True
        
        # 🗺️ Atualizar estado
        if 'estado' in data:
            estado = data['estado'].strip()
            if estado and not Validadores.validar_uf(estado):
                return jsonify({'error': 'UF inválida'}), 400
            
            estado_upper = estado.upper() if estado else None
            if estado_upper != empresa.estado:
                changes.append(f'Estado: {empresa.estado} → {estado_upper}')
                empresa.estado = estado_upper
                updated = True
        
        if updated:
            empresa.atualizado_em = Config.get_current_timestamp()
            
            # 📝 Log de atualização
            log_auditoria = LogAuditoria(
                usuario_id=current_user.id,
                acao='configuracao_empresa_atualizada',
                modulo='company',
                tipo_recurso='empresa',
                recurso_id=empresa.id,
                detalhes=f'Alterações na empresa: {", ".join(changes)}',
                status='sucesso',
                endereco_ip=request.remote_addr,
                agente_usuario=request.user_agent.string
            )
            db.session.add(log_auditoria)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Configurações atualizadas com sucesso' if updated else 'Nenhuma alteração realizada',
            'company': empresa.to_dict()
        })
        
    except Exception as e:
        print(f'❌ Erro ao atualizar configurações: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@company_bp.route('/claim-chat', methods=['POST'])
@login_required
def claim_chat():
    """
    Representante OU Vendedor assume um chat para atendimento humano
    """
    # ✅ CORREÇÃO: Agora vendedores também podem assumir chats!
    if not current_user.pode_gerenciar_empresa():  # Isso inclui cargo 4 (Representante) E 5 (Vendedor)
        return jsonify({'error': 'Apenas usuários empresariais podem assumir chats'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    chat_id = data.get('chat_id')
    
    if not chat_id:
        return jsonify({'error': 'ID do chat é obrigatório'}), 400
    
    try:
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({'error': 'Chat não encontrado'}), 404
        
        # 🔒 Verificar se chat pertence à empresa do usuário
        if chat.empresa_id != current_user.empresa_id:
            return jsonify({'error': 'Chat não pertence à sua empresa'}), 403
        
        # 🔒 Verificar se já está assumido
        if chat.assumido_por_id:
            return jsonify({'error': 'Chat já está sendo atendido'}), 400
        
        # 👥 Assumir o chat
        chat.assumir_chat(current_user.id)
        
        # 📝 Log de chat assumido
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='chat_assumido',
            modulo='company',
            tipo_recurso='chat',
            recurso_id=chat_id,
            detalhes=f'Chat {chat_id} assumido para atendimento humano por {current_user.get_nome_cargo()}',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat assumido com sucesso',
            'chat': chat.to_dict()
        })
        
    except Exception as e:
        print(f'❌ Erro ao assumir chat: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@company_bp.route('/release-chat', methods=['POST'])
@login_required
def release_chat():
    """
    Representante OU Vendedor libera um chat de volta para Amanda AI
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    chat_id = data.get('chat_id')
    
    if not chat_id:
        return jsonify({'error': 'ID do chat é obrigatório'}), 400
    
    try:
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({'error': 'Chat não encontrado'}), 404
        
        # 🔒 Verificar se é o responsável pelo chat
        if chat.assumido_por_id != current_user.id:
            return jsonify({'error': 'Apenas o responsável pode liberar o chat'}), 403
        
        # 🔓 Liberar o chat
        chat.liberar_chat()
        
        # 📝 Log de chat liberado
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='chat_liberado',
            modulo='company',
            tipo_recurso='chat',
            recurso_id=chat_id,
            detalhes=f'Chat {chat_id} liberado para Amanda AI por {current_user.get_nome_cargo()}',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat liberado com sucesso',
            'chat': chat.to_dict()
        })
        
    except Exception as e:
        print(f'❌ Erro ao liberar chat: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@company_bp.route('/my-active-chats', methods=['GET'])
@login_required
def get_my_active_chats():
    """
    Obtém chats ativos assumidos pelo usuário atual
    """
    if not current_user.pode_gerenciar_empresa():
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    if not current_user.empresa_id:
        return jsonify({'error': 'Usuário não vinculado a uma empresa'}), 403
    
    try:
        # 📋 Chats assumidos pelo usuário atual que ainda estão ativos
        meus_chats_ativos = Chat.query.filter_by(
            empresa_id=current_user.empresa_id,
            assumido_por_id=current_user.id,
            status='assumido'
        ).order_by(Chat.assumido_em.desc()).all()
        
        return jsonify({
            'success': True,
            'chats': [chat.to_dict() for chat in meus_chats_ativos],
            'total': len(meus_chats_ativos)
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter chats ativos: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@company_bp.route('/available-chats', methods=['GET'])
@login_required
def get_available_chats():
    """
    Obtém chats disponíveis para atendimento (não assumidos)
    """
    if not current_user.pode_gerenciar_empresa():
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    if not current_user.empresa_id:
        return jsonify({'error': 'Usuário não vinculado a uma empresa'}), 403
    
    try:
        # 📋 Chats ativos não assumidos da empresa
        chats_disponiveis = Chat.query.filter_by(
            empresa_id=current_user.empresa_id,
            status='ativo',
            assumido_por_id=None
        ).order_by(Chat.criado_em.desc()).limit(50).all()
        
        return jsonify({
            'success': True,
            'chats': [chat.to_dict() for chat in chats_disponiveis],
            'total': len(chats_disponiveis)
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter chats disponíveis: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

print("✅ Company routes carregadas com sucesso!")