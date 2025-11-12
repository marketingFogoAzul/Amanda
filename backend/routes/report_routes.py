from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Relatorio, Chat, Usuario, LogAuditoria
from config import Config
from utils.validators import Validadores
from datetime import datetime

report_bp = Blueprint('report', __name__)

@report_bp.route('/create', methods=['POST'])
@login_required
def create_report():
    """
    Cria um report/denúncia sobre um chat
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    chat_id = data.get('chat_id')
    motivo = data.get('motivo', '').strip()
    categoria = data.get('categoria', 'outros')
    
    # 🛡️ Validações
    if not chat_id:
        return jsonify({'error': 'ID do chat é obrigatório'}), 400
    
    if not motivo:
        return jsonify({'error': 'Motivo do report é obrigatório'}), 400
    
    if len(motivo) > 1000:
        return jsonify({'error': 'Motivo muito longo (máximo 1000 caracteres)'}), 400
    
    # 🎯 Categorias válidas
    categorias_validas = ['spam', 'ofensa', 'contato', 'conteudo_improprio', 'outros']
    if categoria not in categorias_validas:
        return jsonify({'error': 'Categoria inválida'}), 400
    
    try:
        # 🔍 Verificar se chat existe
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({'error': 'Chat não encontrado'}), 404
        
        # 🔒 Verificar se o usuário tem acesso ao chat
        if chat.usuario_id != current_user.id and not current_user.eh_admin():
            return jsonify({'error': 'Acesso não autorizado a este chat'}), 403
        
        # 📋 Criar report
        report = Relatorio(
            relator_id=current_user.id,
            chat_id=chat_id,
            motivo=motivo,
            categoria=categoria,
            status='pendente'
        )
        db.session.add(report)
        db.session.flush()  # Para obter o ID
        
        # 📝 Log de criação do report
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='report_criado',
            modulo='report',
            tipo_recurso='report',
            recurso_id=report.id,
            detalhes=f'Report criado para chat {chat_id}. Categoria: {categoria}',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Report criado com sucesso. Nossa equipe irá analisá-lo.',
            'report_id': report.id
        })
        
    except Exception as e:
        print(f'❌ Erro ao criar report: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@report_bp.route('/my-reports', methods=['GET'])
@login_required
def get_my_reports():
    """
    Obtém os reports feitos pelo usuário atual
    """
    try:
        # 📋 Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status', '')
        
        # 🔍 Query base
        query = Relatorio.query.filter_by(relator_id=current_user.id)
        
        # 🎯 Aplicar filtro de status
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # 📊 Ordenar e paginar
        reports = query.order_by(Relatorio.criado_em.desc())\
                      .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'reports': [report.to_dict() for report in reports.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': reports.total,
                'pages': reports.pages
            }
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter reports: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@report_bp.route('/admin/pending', methods=['GET'])
@login_required
def get_pending_reports():
    """
    Obtém reports pendentes (apenas administradores)
    """
    if not current_user.eh_admin():
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    try:
        # 📋 Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 🔍 Reports pendentes
        reports = Relatorio.query.filter_by(status='pendente')\
                               .order_by(Relatorio.criado_em.asc())\
                               .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'reports': [report.to_dict() for report in reports.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': reports.total,
                'pages': reports.pages
            }
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter reports pendentes: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@report_bp.route('/admin/all', methods=['GET'])
@login_required
def get_all_reports():
    """
    Obtém todos os reports (apenas administradores)
    """
    if not current_user.eh_admin():
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    try:
        # 📋 Parâmetros de paginação e filtros
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status', '')
        categoria_filter = request.args.get('categoria', '')
        
        # 🔍 Query base
        query = Relatorio.query
        
        # 🎯 Aplicar filtros
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        if categoria_filter:
            query = query.filter_by(categoria=categoria_filter)
        
        # 📊 Ordenar e paginar
        reports = query.order_by(Relatorio.criado_em.desc())\
                      .paginate(page=page, per_page=per_page, error_out=False)
        
        # 📈 Estatísticas
        total_reports = Relatorio.query.count()
        pendentes = Relatorio.query.filter_by(status='pendente').count()
        em_analise = Relatorio.query.filter_by(status='em_analise').count()
        resolvidos = Relatorio.query.filter_by(status='resolvido').count()
        descartados = Relatorio.query.filter_by(status='descartado').count()
        
        return jsonify({
            'success': True,
            'reports': [report.to_dict() for report in reports.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': reports.total,
                'pages': reports.pages
            },
            'stats': {
                'total': total_reports,
                'pendentes': pendentes,
                'em_analise': em_analise,
                'resolvidos': resolvidos,
                'descartados': descartados
            }
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter todos os reports: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@report_bp.route('/admin/<int:report_id>/analyze', methods=['POST'])
@login_required
def analyze_report(report_id):
    """
    Marca um report como em análise (apenas administradores)
    """
    if not current_user.eh_admin():
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    try:
        report = Relatorio.query.get(report_id)
        
        if not report:
            return jsonify({'error': 'Report não encontrado'}), 404
        
        if not report.esta_pendente():
            return jsonify({'error': 'Apenas reports pendentes podem ser analisados'}), 400
        
        # 🔍 Marcar como em análise
        report.marcar_como_analise(current_user.id)
        
        # 📝 Log de análise
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='report_analisado',
            modulo='report',
            tipo_recurso='report',
            recurso_id=report_id,
            detalhes=f'Report {report_id} marcado como em análise',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Report marcado como em análise',
            'report': report.to_dict()
        })
        
    except Exception as e:
        print(f'❌ Erro ao analisar report: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@report_bp.route('/admin/<int:report_id>/resolve', methods=['POST'])
@login_required
def resolve_report(report_id):
    """
    Resolve um report (apenas administradores)
    """
    if not current_user.eh_admin():
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    resolucao = data.get('resolucao', '').strip()
    acao_tomada = data.get('acao_tomada', 'nenhuma')
    
    if not resolucao:
        return jsonify({'error': 'Descrição da resolução é obrigatória'}), 400
    
    # 🎯 Ações válidas
    acoes_validas = ['nenhuma', 'advertencia', 'suspensao', 'banimento']
    if acao_tomada not in acoes_validas:
        return jsonify({'error': 'Ação tomada inválida'}), 400
    
    try:
        report = Relatorio.query.get(report_id)
        
        if not report:
            return jsonify({'error': 'Report não encontrado'}), 404
        
        if report.esta_resolvido() or report.foi_descartado():
            return jsonify({'error': 'Report já foi processado'}), 400
        
        # 🔧 Aplicar ação se necessário
        if acao_tomada in ['suspensao', 'banimento']:
            usuario_alvo = report.chat.usuario
            if usuario_alvo:
                if acao_tomada == 'suspensao':
                    # ⏳ Suspender por 3 dias
                    suspensao_ate = (datetime.now() + timedelta(days=3)).strftime('%d/%m/%Y %H:%M:%S')
                    usuario_alvo.congelado_ate = suspensao_ate
                    resolucao += f'. Usuário suspenso até {suspensao_ate}'
                else:  # banimento
                    usuario_alvo.banido = True
                    usuario_alvo.motivo_banimento = f'Banido devido a report #{report_id}: {report.motivo}'
                    resolucao += '. Usuário banido permanentemente'
                
                # 📝 Log da ação no usuário
                log_auditoria_usuario = LogAuditoria(
                    usuario_id=current_user.id,
                    acao=f'usuario_{acao_tomada}',
                    modulo='report',
                    tipo_recurso='usuario',
                    recurso_id=usuario_alvo.id,
                    detalhes=f'Usuário {acao_tomada} devido ao report #{report_id}',
                    status='sucesso',
                    endereco_ip=request.remote_addr,
                    agente_usuario=request.user_agent.string
                )
                db.session.add(log_auditoria_usuario)
        
        # ✅ Resolver report
        report.resolver_report(resolucao, acao_tomada, current_user.id)
        
        # 📝 Log de resolução
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='report_resolvido',
            modulo='report',
            tipo_recurso='report',
            recurso_id=report_id,
            detalhes=f'Report {report_id} resolvido. Ação: {acao_tomada}',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Report resolvido com sucesso',
            'report': report.to_dict()
        })
        
    except Exception as e:
        print(f'❌ Erro ao resolver report: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@report_bp.route('/admin/<int:report_id>/discard', methods=['POST'])
@login_required
def discard_report(report_id):
    """
    Descarta um report (apenas administradores)
    """
    if not current_user.eh_admin():
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    motivo = data.get('motivo', '').strip()
    
    if not motivo:
        return jsonify({'error': 'Motivo do descarte é obrigatório'}), 400
    
    try:
        report = Relatorio.query.get(report_id)
        
        if not report:
            return jsonify({'error': 'Report não encontrado'}), 404
        
        if report.esta_resolvido() or report.foi_descartado():
            return jsonify({'error': 'Report já foi processado'}), 400
        
        # 🗑️ Descartar report
        report.descartar_report(motivo, current_user.id)
        
        # 📝 Log de descarte
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='report_descartado',
            modulo='report',
            tipo_recurso='report',
            recurso_id=report_id,
            detalhes=f'Report {report_id} descartado. Motivo: {motivo}',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Report descartado com sucesso',
            'report': report.to_dict()
        })
        
    except Exception as e:
        print(f'❌ Erro ao descartar report: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@report_bp.route('/<int:report_id>', methods=['GET'])
@login_required
def get_report_details(report_id):
    """
    Obtém detalhes de um report específico
    """
    try:
        report = Relatorio.query.get(report_id)
        
        if not report:
            return jsonify({'error': 'Report não encontrado'}), 404
        
        # 🔒 Verificar permissões
        if report.relator_id != current_user.id and not current_user.eh_admin():
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        return jsonify({
            'success': True,
            'report': report.to_dict()
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter detalhes do report: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@report_bp.route('/stats', methods=['GET'])
@login_required
def get_report_stats():
    """
    Obtém estatísticas de reports
    """
    try:
        if current_user.eh_admin():
            # 📊 Estatísticas para administradores
            total_reports = Relatorio.query.count()
            reports_pendentes = Relatorio.query.filter_by(status='pendente').count()
            reports_analise = Relatorio.query.filter_by(status='em_analise').count()
            reports_resolvidos = Relatorio.query.filter_by(status='resolvido').count()
            
            # 📈 Distribuição por categoria
            categorias = db.session.query(
                Relatorio.categoria,
                db.func.count(Relatorio.id)
            ).group_by(Relatorio.categoria).all()
            
            distribuicao_categorias = {cat: count for cat, count in categorias}
            
            return jsonify({
                'success': True,
                'stats': {
                    'total': total_reports,
                    'pendentes': reports_pendentes,
                    'em_analise': reports_analise,
                    'resolvidos': reports_resolvidos,
                    'categorias': distribuicao_categorias
                }
            })
        else:
            # 📊 Estatísticas para usuários comuns
            meus_reports = Relatorio.query.filter_by(relator_id=current_user.id).count()
            meus_pendentes = Relatorio.query.filter_by(relator_id=current_user.id, status='pendente').count()
            meus_resolvidos = Relatorio.query.filter_by(relator_id=current_user.id, status='resolvido').count()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total': meus_reports,
                    'pendentes': meus_pendentes,
                    'resolvidos': meus_resolvidos
                }
            })
        
    except Exception as e:
        print(f'❌ Erro ao obter estatísticas: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

print("✅ Report routes carregadas com sucesso!")