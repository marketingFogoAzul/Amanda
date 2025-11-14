import os

# Define o caminho base do projeto
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    """
    Configuração base e única do sistema, 
    usando a conexão direta do Neon DB.
    """
    # Chaves de Segurança
    SECRET_KEY = "zipbum-amanda-flask-sk-muito-secreto-123"
    JWT_SECRET_KEY = "zipbum-amanda-jwt-sk-muito-secreto-456"
    
    # --- CONEXÃO DIRETA NEON DB ---
    # Conforme solicitado, usando o link direto.
    # 🚨 ATENÇÃO: A senha (fake) está visível no código.
    SQLALCHEMY_DATABASE_URI = "postgresql://neondb_owner:npg_E9grjAHT3ubc@ep-young-cloud-a8makyxk-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # -------------------------------
    
    # Porta Padrão do DB (Não é mais usada pela string, mas inofensivo)
    DB_PORT = "5432"

    # Gemini AI API (Substitua pela sua chave)
    GEMINI_API_KEY = "AIzaSyB5KjpvpnCKgqV0klWM4iVErDbwly5nFOs" 
    GEMINI_MODEL = "gemini-2.5-flash"
    
    # Google reCAPTCHA (Substitua pelas suas chaves)
    RECAPTCHA_SITE_KEY = "6LfhuAssAAAAAI3GfXs_5vif4Uq9d8dj_UAayXvV"
    RECAPTCHA_SECRET_KEY = "6LfhuAssAAAAAEkzx2ZeBH1d82WQgg8J-2HYhkH6"

    # Configurações de Formato
    PYTHON_DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
    TIMEZONE = "America/Sao_Paulo"

    # Configurações de Upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    DEV_SECRET_CODE = "Qazxcvbnmlp7@"

# --- REMOVIDO DevelopmentConfig (localhost) ---

# --- REMOVIDO ProductionConfig ---

# --- REMOVIDO config_by_name dict ---

def get_config():
    """
    Retorna a classe de configuração principal.
    O FLASK_ENV=prod/dev foi removido para usar 
    apenas a conexão direta acima.
    """
    return Config # Retorna a CLASSE Config