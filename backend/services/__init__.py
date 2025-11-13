# backend/services/__init__.py

# Este arquivo transforma o diretório 'services' em um pacote Python.

# Importa os serviços para facilitar o acesso
from .date_service import DateService
from .ai_service import AIService
from .moderation_service import ModerationService
from .role_service import RoleService
# (Futuros serviços)
# from .csv_service import CSVService
# from .negotiation_service import NegotiationService

print("Carregando pacote de serviços (services)...")