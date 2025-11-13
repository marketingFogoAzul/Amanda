# backend/app.py
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS

# Importa nossa função de configuração do config.py
from config import get_config, BASE_DIR

# 1. Inicialização das Extensões
# Elas são criadas fora da função create_app para serem importáveis em outros arquivos
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
cors = CORS()

# Tenta importar a configuração do servidor (host/port)
try:
    from server_config import SERVER_HOST, SERVER_PORT
except ImportError:
    SERVER_HOST = '127.0.0.1'
    SERVER_PORT = 5000

def create_app():
    """
    Application Factory Pattern: Cria e configura a instância do app Flask.
    """
    
    # 2. Criação da Instância do App
    # Ajusta os caminhos de static e templates para apontar para a raiz do projeto
    app = Flask(__name__,
                static_folder=os.path.join(BASE_DIR, 'static'), 
                template_folder=os.path.join(BASE_DIR, 'templates'))
    
    # 3. Carregamento da Configuração
    app_config = get_config()
    app.config.from_object(app_config)
    
    # 4. Inicialização das Extensões com o App
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    
    # Configura o CORS para permitir requisições do frontend
    # Em produção, restrinja a origem (ex: "http://seu-dominio-frontend.com")
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}) # Permite tudo para dev

    # 5. Importação dos Modelos (IMPORTANTE!)
    # Devemos importar os modelos *antes* de registrar os blueprints
    # e *depois* de inicializar o 'db', para que o Flask-Migrate os veja.
    with app.app_context():
        from models import users, companies, chats, negotiations, reports, evaluations, audit_log
        
        # (Opcional) Criar os cargos (roles) iniciais se não existirem
        from models.users import Role
        from utils.constants import CARGOS_NOMES
        if db.session.query(Role).count() == 0:
            print("Criando cargos (roles) iniciais...")
            for level, name in CARGOS_NOMES.items():
                new_role = Role(name=name, permission_level=level)
                db.session.add(new_role)
            db.session.commit()
            print("Cargos criados com sucesso.")

    # 6. Registro dos Blueprints (Rotas)
    # Importa os blueprints do pacote de rotas
    from routes import auth_bp, chat_bp, company_bp, admin_bp, import_bp, negotiation_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(company_bp, url_prefix='/api/company')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(import_bp, url_prefix='/api/import')
    app.register_blueprint(negotiation_bp, url_prefix='/api/negotiation')

    # 7. Importa os callbacks do JWT
    # (Isso associa as funções de security.py ao 'jwt')
    import utils.security

    # 8. Rotas de Teste e Error Handlers
    @app.route('/api/')
    def api_index():
        return jsonify({"message": "Amanda AI - ZIPBUM Backend API is running."})

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not Found", "message": "A URL solicitada não foi encontrada."}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback() # Garante que transações falhas sejam desfeitas
        return jsonify({"error": "Internal Server Error", "message": "Ocorreu um erro interno no servidor."}), 500

    return app

# Ponto de entrada para rodar o servidor
if __name__ == "__main__":
    app = create_app()
    print(f"🚀 Iniciando servidor Amanda AI - ZIPBUM em http://{SERVER_HOST}:{SERVER_PORT}...")
    # Roda o servidor de desenvolvimento do Flask
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=app.config['DEBUG'])