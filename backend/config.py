import os
from datetime import datetime

# 🚨 IMPORTAÇÃO NECESSÁRIA: Utiliza o serviço de timezone para garantir a formatação e o fuso horário
from services.timezone_service import timezone_service 

class Config:
    """
    Configurações globais da aplicação Amanda AI
    """
    
    # 🔐 Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Qazxcvbnmlp7@ZIPBUM2025@@@'
    
    # 🗄️ Banco de Dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://neondb_owner:npg_E9grjAHT3ubc@ep-young-cloud-a8makyxk-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 🤖 Inteligência Artificial
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'AIzaSyB5KjpvpnCKgqV0klWM4iVErDbwly5nFOs'
    
    # 👥 Sistema de Cargos (0-7)
    ROLES = {
        0: 'Desenvolvedor',
        1: 'Júnior', 
        2: 'Marketing & TI',
        3: 'Helper Amanda IA',
        4: 'Representante',
        5: 'Vendedor',
        6: 'Cliente Pro',
        7: 'Cliente Básico'
    }
    
    # 🎯 Configurações da Plataforma
    MAX_LOGIN_ATTEMPTS = 3
    FREEZE_DAYS = 3
    HUMAN_INACTIVITY_MINUTES = 10
    
    # 📞 Padrões de Detecção de Contato
    CONTACT_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'(\+55\s?)?(\(?\d{2}\)?[\s-]?)?\d{4,5}[\s-]?\d{4}',
        'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
        'cnpj': r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
    }
    
    # 🗺️ Estados Brasileiros
    BRAZILIAN_STATES = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
        'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 
        'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão',
        'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais',
        'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE': 'Pernambuco',
        'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima',
        'SC': 'Santa Catarina', 'SP': 'São Paulo', 'SE': 'Sergipe',
        'TO': 'Tocantins'
    }
    
    # 💼 Configurações de Negociação
    NEGOTIATION = {
        'max_counteroffers': 2,
        'min_quantity_step': 2,
        'price_increment_percentage': 0.10
    }
    
    # 📊 Configurações de Importação
    IMPORT = {
        'allowed_extensions': {'csv', 'xlsx', 'xls'},
        'max_file_size': 50 * 1024 * 1024,  # 50MB
        'required_columns': ['produto', 'quantidade', 'preco']
    }
    
    # 🔑 Códigos de Ativação
    DEVELOPER_SECRET = 'Qazxcvbnmlp7@'
    
    @staticmethod
    def get_current_timestamp():
        """
        Retorna timestamp atual no formato DD/MM/YYYY HH:MM:SS (América/São Paulo)
        """
        # 🔄 Implementação agora usa o TimezoneService
        return timezone_service.get_current_timestamp()
    
    @staticmethod
    def get_role_name(role_id):
        """
        Retorna o nome do cargo baseado no ID
        """
        return Config.ROLES.get(role_id, 'Desconhecido')
    
    @staticmethod
    def can_assign_roles(role_id):
        """
        Verifica se o cargo pode atribuir outros cargos
        """
        return role_id in [0, 1, 2, 3]
    
    @staticmethod
    def can_manage_company(role_id):
        """
        Verifica se o cargo pode gerenciar empresa
        """
        return role_id in [4, 5]
    
    @staticmethod
    def is_admin(role_id):
        """
        Verifica se é cargo administrativo
        """
        return role_id in [0, 1, 2, 3]
    
    @staticmethod
    def is_company_user(role_id):
        """
        Verifica se é usuário de empresa
        """
        return role_id in [4, 5]
    
    @staticmethod
    def is_client(role_id):
        """
        Verifica se é cliente
        """
        return role_id in [6, 7]
    
    @staticmethod
    def validate_uf(uf):
        """
        Valida se a UF é válida
        """
        return uf.upper() in Config.BRAZILIAN_STATES
    
    @staticmethod
    def get_uf_name(uf):
        """
        Retorna o nome completo do estado
        """
        return Config.BRAZILIAN_STATES.get(uf.upper(), 'Desconhecido')