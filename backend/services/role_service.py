# backend/services/role_service.py

from typing import List  # LINHA CRÍTICA QUE ESTAVA FALTANDO
from models.users import User, Role
from utils.constants import Cargos
from app import db
from functools import wraps
from utils.security import get_user_identity, get_user_role_from_token, jwt_required
from flask import jsonify

class RoleService:
    """
    Serviço para gerenciamento de Cargos (Roles) e Permissões.
    """

    @staticmethod
    def get_role_by_level(level: int) -> Role:
        """Encontra um objeto Role pelo seu nível (0-7)."""
        return Role.query.filter_by(permission_level=level).first()

    @staticmethod
    def change_user_role(user_id: str, new_role_id: int) -> bool:
        """Muda o cargo de um usuário (usando o ID do cargo)."""
        try:
            user = User.query.get(user_id)
            new_role = Role.query.get(new_role_id)
            
            if not user or not new_role:
                return False
                
            user.role_id = new_role.id
            db.session.commit()
            
            # (Futuro) Registrar no AuditLog
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao trocar cargo: {e}")
            return False

    @staticmethod
    def change_user_role_by_level(user_id: str, new_role_level: int) -> bool:
        """Muda o cargo de um usuário (usando o NÍVEL do cargo, 0-7)."""
        new_role = RoleService.get_role_by_level(new_role_level)
        if not new_role:
            print(f"Cargo com nível {new_role_level} não encontrado.")
            return False
            
        return RoleService.change_user_role(user_id, new_role.id)

    @staticmethod
    def is_admin(user: User) -> bool:
        """Verifica se o usuário é Admin ZIPBUM (Nível 0)."""
        return user.role.permission_level == Cargos.ADMIN_ZIPBUM
        
    @staticmethod
    def is_helper(user: User) -> bool:
        """Verifica se o usuário é qualquer tipo de Helper (1, 2, ou 3)."""
        levels = [Cargos.HELPER_N1, Cargos.HELPER_N2, Cargos.HELPER_N3]
        return user.role.permission_level in levels

    @staticmethod
    def is_company_user(user: User) -> bool:
        """Verifica se é Representante ou Vendedor (4 ou 5)."""
        levels = [Cargos.REPRESENTANTE, Cargos.VENDEDOR]
        return user.role.permission_level in levels

# --- Decorator de Permissão ---

def roles_required(levels: List[int]):
    """
    Decorator para proteger rotas, exigindo um nível de permissão (cargo).
    Ex: @roles_required([Cargos.ADMIN_ZIPBUM, Cargos.HELPER_N1])
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Primeiro, verifica se o usuário está logado (JWT Válido)
            try:
                # Chama o decorator do jwt_required
                jwt_required_decorator = jwt_required()
                jwt_required_decorator(lambda: None)() # Executa a verificação
            except Exception as e:
                # Se falhar (token ausente, expirado), retorna o erro padrão
                return jsonify({"error": "Token de autorização ausente ou inválido"}), 401
            
            # Se o token é válido, pega o cargo (role) de dentro dele
            role_level = get_user_role_from_token()
            
            if role_level is None:
                return jsonify({"error": "Token inválido, 'role' não encontrada."}), 401
            
            # Verifica se o cargo do token está na lista de níveis permitidos
            if role_level not in levels:
                return jsonify({"error": "Permissão negada. Seu cargo não permite acesso."}), 403
            
            # Se passou, permite o acesso à rota
            return fn(*args, **kwargs)
        return wrapper
    return decorator