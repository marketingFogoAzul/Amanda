# backend/utils/security.py

from app import bcrypt, jwt
from flask_jwt_extended import (
    create_access_token as flask_create_access_token,
    create_refresh_token,
    jwt_required as flask_jwt_required,
    get_jwt_identity,
    get_jwt
)
import datetime

# --- Gerenciamento de Senhas (Bcrypt) ---

def hash_password(password: str) -> str:
    """
    Gera um hash seguro para uma senha.
    """
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(password_hash: str, password: str) -> bool:
    """
    Verifica se a senha fornecida corresponde ao hash.
    """
    return bcrypt.check_password_hash(password_hash, password)

# --- Gerenciamento de Token (JWT) ---

def create_access_token(identity, expires_delta=datetime.timedelta(hours=1)):
    """
    Cria um token de acesso JWT.
    A 'identity' é geralmente o ID do usuário.
    """
    return flask_create_access_token(identity=identity, expires_delta=expires_delta)

def create_refresh_token(identity):
    """
    Cria um token de atualização (refresh token).
    """
    return create_refresh_token(identity=identity)

def get_user_identity():
    """
    Retorna a 'identity' (ID do usuário) do token JWT atual.
    Deve ser usado dentro de uma rota protegida.
    """
    return get_jwt_identity()

def get_user_role_from_token():
    """
    Função personalizada para obter o 'cargo' (role) 
    que adicionamos ao token.
    """
    claims = get_jwt()
    # Usamos .get() para evitar erro se o 'role' não estiver no token
    return claims.get("role", None)

# --- Proteção de Rotas ---

# Re-exporta o decorator para uso fácil
jwt_required = flask_jwt_required

# --- Funções de Callback do JWT (usadas no app.py) ---

@jwt.user_identity_loader
def user_identity_lookup(user):
    """
    Define qual parte do objeto 'user' será armazenada 
    como 'identity' no token. Usamos o ID.
    """
    return user.id

@jwt.additional_claims_loader
def add_claims_to_access_token(user):
    """
    Adiciona informações extras (claims) ao token de acesso.
    Vamos adicionar o nível de permissão (role) aqui.
    Isso é SUPER útil para o frontend e backend.
    """
    if hasattr(user, 'role') and user.role:
        return {"role": user.role.permission_level}
    # Caso o usuário seja carregado de outra forma (ex: refresh token)
    if isinstance(user, str):
        from models.users import User
        u = User.query.get(user)
        if u and u.role:
            return {"role": u.role.permission_level}
    return {}

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """
    Define como carregar o objeto 'User' completo
    a partir da 'identity' (ID) do token.
    Isso é usado pelo @jwt_required(fresh=True) ou get_current_user()
    """
    from models.users import User # Importação local
    identity = jwt_data["sub"] # 'sub' é o campo padrão para 'identity'
    return User.query.get(identity)