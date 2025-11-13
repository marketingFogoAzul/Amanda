# backend/config.py
import os

# Define o caminho base do projeto
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    """
    Configuração base. Contém todas as chaves e configurações
    que são compartilhadas ou que possuem um padrão.
    """
    
    # Chaves de Segurança
    SECRET_KEY = "zipbum-amanda-flask-sk-muito-secreto-123"
    JWT_SECRET_KEY = "zipbum-amanda-jwt-sk-muito-secreto-456" # Usado pelo Flask-JWT-Extended
    
    # Banco de Dados (Valores Padrão)
    DB_USER = "postgres"
    DB_PASSWORD = "password" 
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "zipbum_db"
    
    # ⚠️ SUA CHAVE DE PRODUÇÃO ESTÁ NO LUGAR ERRADO (AQUI)
    # Substitua o marcador pela sua string de conexão
    SQLALCHEMY_DATABASE_URI = "postgresql://neondb_owner:npg_E9grjAHT3ubc@ep-young-cloud-a8makyxk-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ⚠️ SUAS CHAVES GEMINI ESTÃO NO LUGAR ERRADO (AQUI)
    # Substitua o marcador pela sua chave
    GEMINI_API_KEY = "AIzaSyB5KjpvpnCKgqV0klWM4iVErDbwly5nFOs"
    GEMINI_MODEL = "gemini-2.5-flash"
    
    # ⚠️ SUAS CHAVES RECAPTCHA ESTÃO NO LUGAR ERRADO (AQUI)
    # Substitua os marcadores pelas suas chaves
    RECAPTCHA_SITE_KEY = "6LfhuAssAAAAAI3GfXs_5vif4Uq9d8dj_UAayXvV"
    RECAPTCHA_SECRET_KEY = "6LfhuAssAAAAAEkzx2ZeBH1d82WQgg8J-2HYhkH6"

    # Configurações de Formato
    PYTHON_DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
    TIMEZONE = "America/Sao_Paulo"

    # Configurações de Upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # Limite de 16MB

    # Código Secreto Developer
    DEV_SECRET_CODE = "Qazxcvbnmlp7@"

class DevelopmentConfig(Config):
    """Configuração de Desenvolvimento"""
    DEBUG = True
    TESTING = False
    DB_HOST = "localhost" # Mantém o localhost para dev
    
    # ⚠️ ISTO VAI SOBRESCREVER A CHAVE DO NEON DB
    SQLALCHEMY_DATABASE_URI = f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"

class ProductionConfig(Config):
    """Configuração de Produção"""
    DEBUG = False
    TESTING = False
    
    # Dados de exemplo - (SEUS DADOS REAIS DEVERIAM ESTAR AQUI)
    DB_HOST = "ep-exemplo-neon-host-123456.sa-east-1.aws.neon.tech" 
    DB_USER = "usuarioprod"
    DB_PASSWORD = "senha_prod_forte_hardcoded"
    DB_NAME = "zipbum_prod_db"
    
    # ⚠️ ISTO TAMBÉM VAI SOBRESCREVER A CHAVE DO NEON DB
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{Config.DB_PORT}/{DB_NAME}?sslmode=require"

# Dicionário para facilitar a seleção da configuração
config_by_name = dict(
    dev=DevelopmentConfig,
    prod=ProductionConfig
)

# Função auxiliar para obter a configuração com base em uma variável de ambiente (se definida)
def get_config():
    """Retorna a classe de configuração apropriada."""
    env = os.getenv("FLASK_ENV", "dev")
    return config_by_name.get(env, DevelopmentConfig) # Padrão é Development