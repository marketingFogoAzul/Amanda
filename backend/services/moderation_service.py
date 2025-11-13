# backend/services/moderation_service.py
import re
from typing import Tuple
from models.users import User
from services.date_service import DateService
from app import db

class ModerationService:
    """
    Serviço para moderar conteúdo de mensagens e aplicar bloqueios.
    """
    
    # Regex para detectar dados sensíveis (pode ser melhorado)
    # Regex de Email
    EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # Regex de Telefone (simplificado para Brasil)
    PHONE_REGEX = r'\b(?:\(?\d{2}\)?\s?)?(?:9\d{4}|\d{4})[-\s]?\d{4}\b'
    # Regex de CPF (com ou sem máscara)
    CPF_REGEX = r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'
    # Regex de CNPJ (com ou sem máscara)
    CNPJ_REGEX = r'\b\d{2}\.?\d{3}\.?\d{3}\/\d{4}-?\d{2}\b'
    
    # Links
    LINK_REGEX = r'\b(?:https?:\/\/|www\.)[^\s]+\b'
    
    REGEX_PATTERNS = {
        "email": EMAIL_REGEX,
        "telefone": PHONE_REGEX,
        "cpf": CPF_REGEX,
        "cnpj": CNPJ_REGEX,
        "link": LINK_REGEX,
    }

    @staticmethod
    def check_message(content: str) -> Tuple[bool, str]:
        """
        Verifica se uma mensagem contém conteúdo proibido.
        Retorna (True, "motivo") se for proibido, ou (False, None).
        """
        for reason, pattern in ModerationService.REGEX_PATTERNS.items():
            if re.search(pattern, content, re.IGNORECASE):
                print(f"[Moderação] Conteúdo detectado: {reason}")
                return (True, f"Detecção de {reason}")
                
        return (False, None)

    @staticmethod
    def apply_block(user: User, reason: str, days: int = 3):
        """
        Aplica um bloqueio de 'days' dias a um usuário.
        """
        try:
            now = DateService.get_now()
            blocked_until = DateService.add_days(now, days)
            
            user.is_blocked = True
            user.blocked_until = blocked_until
            
            # (Opcional, mas recomendado) Mudar o cargo do usuário
            # from services.role_service import RoleService
            # RoleService.change_user_role_by_level(user.id, Cargos.BLOQUEADO)
            
            db.session.commit()
            print(f"[Moderação] Usuário {user.email} bloqueado até {blocked_until} por {reason}.")
            
            # (Futuro) Registrar no AuditLog
            # ...
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao aplicar bloqueio no usuário {user.email}: {e}")

    @staticmethod
    def get_block_message(reason: str) -> str:
        """
        Retorna a mensagem padronizada que substitui o conteúdo bloqueado.
        """
        return f"[ MENSAGEM BLOQUEADA ]\nMotivo: {reason}. A troca de informações de contato (email, telefone, etc.) não é permitida nesta plataforma. O usuário foi notificado e bloqueado por 3 dias."