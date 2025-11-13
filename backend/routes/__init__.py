# backend/routes/__init__.py

from flask import Blueprint

# Cria os "Blueprints" para cada conjunto de rotas.
# Um Blueprint é como um "mini-aplicativo" que agrupa rotas relacionadas.

# Blueprint para Autenticação (/api/auth)
auth_bp = Blueprint('auth_bp', __name__)

# Blueprint para Chat e Amanda AI (/api/chat)
chat_bp = Blueprint('chat_bp', __name__)

# Blueprint para o Painel da Empresa (/api/company)
company_bp = Blueprint('company_bp', __name__)

# Blueprint para o Painel Admin ZIPBUM (/api/admin)
admin_bp = Blueprint('admin_bp', __name__)

# Blueprint para Upload de Planilhas (/api/import)
import_bp = Blueprint('import_bp', __name__)

# Blueprint para Ações de Negociação (/api/negotiation)
negotiation_bp = Blueprint('negotiation_bp', __name__)


# Agora, importamos os arquivos de rotas para que o Python 
# "veja" as funções @route.py que estão neles.
# É importante que esta importação venha DEPOIS da criação dos Blueprints.

from . import auth, chat, company, admin, import_routes, negotiation

print("Carregando pacote de rotas (routes)...")