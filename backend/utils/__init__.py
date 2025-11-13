# backend/utils/__init__.py

# Este arquivo transforma o diretório 'utils' em um pacote Python.

# Importa as classes e funções mais usadas para facilitar
# o acesso a partir de outros módulos.
from .constants import CARGOS, CATEGORIAS_DENUNCIA, STATUS_NEGOCIACAO
from .validators import (
    validate_email,
    validate_password_strength,
    validate_cnpj,
    format_cnpj,
    clean_cnpj
)
from .security import (
    hash_password,
    check_password,
    create_access_token,
    get_user_identity,
    jwt_required
)

print("Carregando pacote de utilitários (utils)...")