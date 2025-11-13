# backend/services/date_service.py

import datetime
from dateutil import tz # Para lidar com fusos horários
from config import get_config

# Carrega a configuração para obter o fuso horário e o formato
app_config = get_config()

class DateService:
    """
    Serviço centralizado para manipulação de datas e horas.
    Garante o uso do fuso horário (America/Sao_Paulo) e 
    formato (DD/MM/YYYY HH:MM:SS) corretos.
    """
    
    # Define os fusos
    TIMEZONE_STR = app_config.TIMEZONE # "America/Sao_Paulo"
    TIMEZONE = tz.gettz(TIMEZONE_STR)
    UTC_TIMEZONE = tz.gettz('UTC')
    
    # Define o formato padrão do Python
    DATE_FORMAT = app_config.PYTHON_DATE_FORMAT # "%d/%m/%Y %H:%M:%S"

    @staticmethod
    def get_now() -> datetime.datetime:
        """
        Retorna o datetime 'agora' no fuso horário correto (America/Sao_Paulo).
        """
        # Pega a hora atual em UTC
        now_utc = datetime.datetime.now(tz=DateService.UTC_TIMEZONE)
        # Converte para o fuso de São Paulo
        return now_utc.astimezone(DateService.TIMEZONE)

    @staticmethod
    def format_date(dt: datetime.datetime) -> str:
        """
        Formata um objeto datetime para a string padrão do sistema (DD/MM/YYYY HH:MM:SS).
        """
        if not dt:
            return None
        
        # Se o datetime não tiver fuso, assume que é o fuso local do sistema
        if dt.tzinfo is None:
            dt = dt.astimezone(DateService.TIMEZONE)
            
        return dt.strftime(DateService.DATE_FORMAT)

    @staticmethod
    def parse_date(date_str: str) -> datetime.datetime:
        """
        Converte uma string formatada (DD/MM/YYYY HH:MM:SS) 
        de volta para um objeto datetime com o fuso correto.
        """
        try:
            # Faz o parse da string
            dt = datetime.datetime.strptime(date_str, DateService.DATE_FORMAT)
            # Adiciona a informação de fuso horário
            dt = dt.replace(tzinfo=DateService.TIMEZONE)
            return dt
        except Exception as e:
            print(f"Erro ao fazer parse da data: {e}")
            return None

    @staticmethod
    def add_days(dt: datetime.datetime, days: int) -> datetime.datetime:
        """
        Adiciona dias a um datetime.
        """
        return dt + datetime.timedelta(days=days)

# --- Exemplo de uso (não faz parte do arquivo) ---
# if __name__ == "__main__":
#     service = DateService()
#     agora = service.get_now()
    
#     print(f"Fuso: {service.TIMEZONE_STR}")
#     print(f"Agora (objeto): {agora}")
#     print(f"Agora (formatado): {service.format_date(agora)}")
    
#     data_string = "10/11/2025 15:30:00"
#     print(f"Parse (string): {data_string}")
#     print(f"Parse (objeto): {service.parse_date(data_string)}")