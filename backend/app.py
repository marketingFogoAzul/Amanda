from flask import Flask, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, current_user, login_required
from flask_cors import CORS
from config import Config
from models import db, Usuario
import google.generativeai as genai
import os
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# Configuração de logging para depuração
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app() -> Flask:
    """
    Factory function para criar e configurar a aplicação Flask (API Pura).
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 🔧 Inicializar extensões
    db.init_app(app)
    
    # 🌐 Configurar CORS para frontend
    # CORREÇÃO: Adicionamos a porta 5173 na lista de origens seguras (Vite)
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"], supports_credentials=True)
    
    # 🤖 Configurar Gemini AI
    try:
        api_key = app.config['GEMINI_API_KEY']
        if api_key and api_key != 'sua-chave-gemini-aqui':
            genai.configure(api_key=api_key)
            logger.info("✅ Gemini AI configurado com sucesso")
        else:
            logger.warning("⚠️  Aviso: Chave Gemini não configurada - usando respostas padrão")
    except Exception as e:
        logger.error(f"❌ Erro ao configurar Gemini AI: {e}")
    
    # 🔐 Configurar Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    
    @login_manager.user_loader
    def load_user(user_id):
        """
        Callback para carregar usuário a partir da sessão
        """
        return Usuario.query.get(int(user_id))
    
    # 🔄 Registrar Blueprints (Rotas)
    from routes.auth_routes import auth_bp
    from routes.chat_routes import chat_bp
    from routes.company_routes import company_bp
    from routes.import_routes import import_bp
    from routes.report_routes import report_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(company_bp, url_prefix='/api/company')
    app.register_blueprint(import_bp, url_prefix='/api/import')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    
    # 🏠 Rotas de Redirecionamento (Entrada do Sistema)
    @app.route('/')
    def index():
        """
        Rota principal - Redireciona o navegador para o Frontend React (Vite).
        ✅ CORREÇÃO: Aponta para a porta 5173 do Vite, corrigindo o ERR_CONNECTION_REFUSED.
        """
        logger.info("Redirecionando rota raiz para o Frontend (porta 5173).")
        return redirect("http://localhost:5173")
    
    
    # --- Rota de Segurança Central (Verifica permissões de Painéis no Backend) ---
    
    @app.route('/api/access-check/<string:panel_name>', methods=['GET'])
    @login_required
    def access_check(panel_name: str):
        """
        Verifica no Backend se o usuário tem permissão para acessar um painel específico
        antes de o Frontend carregar o componente.
        """
        user_cargo = current_user.cargo
        
        permission_map = {
            'admin': Config.is_admin(user_cargo),             # Cargos 0-3
            'company': Config.can_manage_company(user_cargo), # Cargos 4-5
            'import': current_user.pode_fazer_upload()        # Cargos 0-3
        }

        has_permission = permission_map.get(panel_name.lower(), False)

        if has_permission:
            logger.info(f"Acesso permitido ao painel '{panel_name}' para usuário ID {current_user.id}")
            return jsonify({'success': True, 'message': 'Acesso autorizado'}), 200
        else:
            logger.warning(f"Acesso negado ao painel '{panel_name}' para usuário ID {current_user.id}")
            return jsonify({'success': False, 'error': 'Acesso não autorizado ao painel.'}), 403

    
    # 🔌 API Routes
    @app.route('/api/user/profile')
    @login_required
    def get_user_profile():
        """
        API para obter perfil completo do usuário atual.
        """
        try:
            return jsonify(current_user.to_dict())
        except Exception as e:
            logger.error(f"Erro ao obter perfil: {e}")
            return jsonify({'error': 'Erro ao obter perfil'}), 500
    
    @app.route('/api/system/health')
    def health_check():
        """
        Health check da aplicação.
        """
        return jsonify({
            'status': 'healthy',
            'timestamp': Config.get_current_timestamp(),
            'version': '1.0.0',
            'platform': 'Amanda AI - Plataforma de Negociação'
        })
    
    @app.route('/api/system/status')
    @login_required
    def system_status():
        """
        Status do sistema (apenas para administradores).
        """
        if not current_user.eh_admin():
            return jsonify({'error': 'Acesso não autorizado'}), 403
            
        # Importa os modelos aqui para evitar erro circular de dependência no topo
        from models import Chat, Usuario, Empresa, Relatorio, LogImportacao
        try:
            stats = {
                'total_users': Usuario.query.count(),
                'total_companies': Empresa.query.count(),
                'active_chats': Chat.query.filter_by(status='ativo').count(),
                'closed_chats': Chat.query.filter_by(status='fechado').count(),
                'pending_reports': Relatorio.query.filter_by(status='pendente').count(),
                'total_imports': LogImportacao.query.count(),
                'system_time': Config.get_current_timestamp()
            }
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Erro ao obter status do sistema: {e}")
            return jsonify({'error': f'Erro interno ao obter status: {e}'}), 500
    
    # ⚠️ Manipuladores de Erro (Retornam JSON para o Frontend)
    # Garante que as rotas de API e as rotas raiz do Flask retornem JSON em vez de HTML inexistente.
    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f"404: Endpoint não encontrado: {request.path}")
        return jsonify({'error': 'Endpoint não encontrado'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500: Erro interno no servidor: {error}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        logger.warning(f"403: Acesso negado para {request.path}")
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        logger.info("401: Tentativa de acesso não autenticado.")
        return jsonify({'error': 'Não autenticado'}), 401
    
    # 🔧 Context Processor (Mantido, mas não renderiza templates)
    @app.context_processor
    def inject_config():
        return dict(
            Config=Config,
            current_year=datetime.now().year,
            platform_name="Amanda AI",
            assistant_name="Amanda"
        )
    
    # ⏰ Before Request - Atualizar última atividade
    @app.before_request
    def update_last_activity():
        if current_user.is_authenticated:
            session['last_activity'] = datetime.now().isoformat()
    
    return app

# 🚀 Inicialização da Aplicação
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        try:
            # 🗄️ Criar tabelas do banco de dados
            db.create_all()
            logger.info("✅ Banco de dados inicializado com sucesso!")
            
            # 🔍 Verificar se existe usuário admin
            from models import Usuario
            admin_user = Usuario.query.filter_by(cargo=0).first()
            if not admin_user:
                logger.info("💡 Dica: Use o código de desenvolvedor para ativar uma conta admin")
            
            logger.info(f"📍 Ambiente: {'Desenvolvimento' if app.debug else 'Produção'}")
            logger.info("🚀 Servidor Amanda AI iniciando...")
            
        except Exception as e:
            logger.critical(f"❌ Erro ao inicializar banco de dados: {e}")
            logger.critical("💡 Verifique a conexão com o banco de dados")
    
    # 🌐 Iniciar servidor
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000,
        threaded=True
    )