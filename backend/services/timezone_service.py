from datetime import datetime
from dateutil import tz
from typing import Optional

class TimezoneService:
    """
    Serviço dedicado à gestão de fusos horários e à geração de timestamps
    em conformidade com o padrão da plataforma: América/São Paulo e formato DD/MM/YYYY HH:MM:SS.
    """

    # Constantes baseadas na configuração da aplicação
    TIMEZONE_STR = 'America/Sao_Paulo'
    TIMESTAMP_FORMAT = '%d/%m/%Y %H:%M:%S'

    def __init__(self):
        """Inicializa o objeto de fuso horário para 'America/Sao_Paulo'."""
        # Obtém as informações do fuso horário de São Paulo
        self.tz_info = tz.gettz(self.TIMEZONE_STR)

    def get_current_datetime(self) -> datetime:
        """
        Retorna o objeto datetime atual no fuso horário configurado (America/Sao_Paulo).
        """
        # Cria um objeto datetime com consciência de fuso horário
        return datetime.now(self.tz_info)

    def get_current_timestamp(self) -> str:
        """
        Retorna o timestamp atual no formato 'DD/MM/YYYY HH:MM:SS'.
        """
        current_dt = self.get_current_datetime()
        return current_dt.strftime(self.TIMESTAMP_FORMAT)

    def format_datetime_to_timestamp(self, dt_object: datetime) -> str:
        """
        Formata um objeto datetime existente para o formato padrão.
        """
        # Se o objeto tiver fuso horário, converte para a string formatada
        if dt_object.tzinfo:
            dt_object = dt_object.astimezone(self.tz_info)
        
        return dt_object.strftime(self.TIMESTAMP_FORMAT)
    
    def parse_timestamp_to_datetime(self, timestamp_str: str, timezone_aware: bool = True) -> Optional[datetime]:
        """
        Converte uma string de timestamp no formato padrão de volta para um objeto datetime.
        """
        try:
            dt_object = datetime.strptime(timestamp_str, self.TIMESTAMP_FORMAT)
            
            if timezone_aware:
                # Atribui o fuso horário de São Paulo
                return dt_object.replace(tzinfo=self.tz_info)
            return dt_object
            
        except ValueError:
            return None

# Instância Singleton para ser importada e utilizada globalmente
timezone_service = TimezoneService()