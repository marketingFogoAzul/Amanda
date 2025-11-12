from flask import Flask, render_template, request, jsonify, session, redirect, url_for # <-- redirect e url_for adicionados
from flask_login import LoginManager, current_user, login_required
from flask_cors import CORS
from config import Config
from models import db, Usuario
import google.generativeai as genai
import os
from datetime import datetime

def create_app():
    """
    Factory function para criar e configurar a aplicação Flask
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 🔧 Inicializar extensões
    db.init_app(app)
    
    # 🌐 Configurar CORS para frontend
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"], supports_credentials=True)
    
    # 🤖 Configurar Gemini AI
    try:
        if app.config['GEMINI_API_KEY'] and app.config['GEMINI_API_KEY'] != 'sua-chave-gemini-aqui':
            genai.configure(api_key=app.config['GEMINI_API_KEY'])
            print("✅ Gemini AI configurado com sucesso")
        else:
            print("⚠️  Aviso: Chave Gemini não configurada - usando respostas padrão")
    except Exception as e:
        print(f"❌ Erro ao configurar Gemini AI: {e}")
    
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
    
    # 🏠 Rotas Principais (Redirecionamento para o Frontend)
    @app.route('/')
    def index():
        """
        Rota principal - Redireciona o navegador para o Frontend React.
        Remove as chamadas render_template para login.html.
        """
        return redirect("http://localhost:3000")
    
    # NOTA: As rotas /dashboard, /chat, /company-panel e /admin-panel 
    # foram removidas/comentadas, pois o roteamento é feito pelo React.
    
    # 🔌 API Routes
    @app.route('/api/user/profile')
    @login_required
    def get_user_profile():
        """
        API para obter perfil do usuário atual
        """
        try:
            user_data = current_user.to_dict()
            return jsonify(user_data)
        except Exception as e:
            print(f"Erro ao obter perfil: {e}")
            return jsonify({'error': 'Erro ao obter perfil'}), 500
    
    @app.route('/api/system/health')
    def health_check():
        """
        Health check da aplicação
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
        Status do sistema (apenas para administradores)
        """
        if not current_user.eh_admin():
            return jsonify({'error': 'Acesso não autorizado'}), 403
            
        from models import Chat, Usuario, Empresa
        try:
            stats = {
                'total_users': Usuario.query.count(),
                'total_companies': Empresa.query.count(),
                'active_chats': Chat.query.filter_by(status='ativo').count(),
                'closed_chats': Chat.query.filter_by(status='fechado').count(),
                'system_time': Config.get_current_timestamp()
            }
            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': f'Erro ao obter status: {e}'}), 500
    
    # ⚠️ Manipuladores de Erro
    # NOTA: Manipuladores de erro de API (que retornam JSON) são mantidos.
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint não encontrado'}), 404
        # Remove render_template:
        return jsonify({'error': 'Página não encontrada'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Erro interno do servidor'}), 500
        # Remove render_template:
        return jsonify({'error': 'Erro interno do servidor'}), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Acesso não autorizado'}), 403
        # Remove render_template:
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Não autenticado'}), 401
        # Remove render_template:
        return jsonify({'error': 'Não autenticado'}), 401
    
    # 🔧 Context Processor - Variáveis globais para templates (APENAS se ainda usar templates)
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
            # NOTA: datetime.now() deve ser substituído por timezone_service.get_current_datetime()
            # para garantir a conformidade com o fuso horário.
            session['last_activity'] = datetime.now().isoformat()
    
    return app

# 🚀 Inicialização da Aplicação
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        try:
            # 🗄️ Criar tabelas do banco de dados
            db.create_all()
            print("✅ Banco de dados inicializado com sucesso!")
            
            # 🔍 Verificar se existe usuário admin
            from models import Usuario
            admin_user = Usuario.query.filter_by(cargo=0).first()
            if not admin_user:
                print("💡 Dica: Use o código de desenvolvedor para ativar uma conta admin")
            
            # NOTA: O ambiente é "Desenvolvimento" se app.debug for True (que é o caso)
            print(f"📍 Ambiente: {'Desenvolvimento' if app.debug else 'Produção'}")
            print("🚀 Servidor Amanda AI iniciando...")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar banco de dados: {e}")
            print("💡 Verifique a conexão com o banco de dados")
    
    # 🌐 Iniciar servidor
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000,
        threaded=True
    )