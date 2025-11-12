import re
from typing import Tuple, Optional

# Importa a classe Config para acesso a constantes como estados e padrões de contato
from config import Config 

class Validadores: # <--- A classe DEVE ter essa exata capitalização (Validadores)
    """
    Coleção de métodos estáticos para validação de dados de entrada,
    garantindo a conformidade com as regras de negócio e padrões de segurança.
    """
    
    # --- Validação de Usuário e Autenticação ---

    @staticmethod
    def validar_email(email: str) -> bool:
        """Valida o formato básico de um e-mail."""
        if not email:
            return False
        # Expressão regular simples para formato de e-mail (usada em auth_routes)
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.fullmatch(email_regex, email) is not None

    @staticmethod
    def validar_senha(password: str) -> Tuple[bool, str]:
        """
        Valida a senha com requisitos de segurança:
        - Mínimo de 8 caracteres.
        - Pelo menos uma letra maiúscula, uma minúscula e um número.
        """
        if len(password) < 8:
            return False, 'A senha deve ter no mínimo 8 caracteres.'
        if not re.search(r'[A-Z]', password):
            return False, 'A senha deve conter pelo menos uma letra maiúscula.'
        if not re.search(r'[a-z]', password):
            return False, 'A senha deve conter pelo menos uma letra minúscula.'
        if not re.search(r'[0-9]', password):
            return False, 'A senha deve conter pelo menos um número.'
        
        return True, 'Senha válida.'

    @staticmethod
    def validar_nome(full_name: str) -> Tuple[bool, str]:
        """
        Valida o nome completo:
        - Não pode estar vazio.
        - Mínimo de 3 caracteres.
        """
        if not full_name or full_name.strip() == '':
            return False, 'O nome completo é obrigatório.'
        if len(full_name) < 3:
            return False, 'O nome deve ter no mínimo 3 caracteres.'
        
        return True, 'Nome válido.'

    # --- Validação de Localização e Endereço ---

    @staticmethod
    def validar_uf(uf: str) -> bool:
        """Valida se a UF (estado brasileiro) é válida."""
        # Assume que Config.validate_uf está implementado
        return Config.validate_uf(uf)

    @staticmethod
    def validar_endereco(address: Optional[str]) -> Tuple[bool, str]:
        """
        Valida a string de endereço (opcional, mas deve ter um tamanho razoável se fornecido).
        """
        if not address or address.strip() == '':
            return True, 'Endereço opcional, não fornecido.'
        
        if len(address) > 300:
            return False, 'O endereço é muito longo (máximo 300 caracteres).'
        
        return True, 'Endereço válido.'
    
    @staticmethod
    def validar_telefone(telefone: str) -> bool:
        """
        Valida um formato básico de telefone/celular (apenas dígitos).
        """
        clean_phone = re.sub(r'\D', '', telefone)
        
        return 10 <= len(clean_phone) <= 11

    # --- Validação de Chat e Reports ---

    @staticmethod
    def validar_mensagem_chat(message: str) -> Tuple[bool, str]:
        """
        Valida o conteúdo e tamanho de uma mensagem de chat.
        """
        if not message or message.strip() == '':
            return False, 'A mensagem não pode ser vazia.'
        if len(message) > 5000: 
            return False, 'A mensagem é muito longa.'
            
        return True, 'Mensagem válida.'

    @staticmethod
    def validar_avaliacao(rating: Optional[int]) -> bool:
        """
        Valida se a nota da avaliação está entre 1 e 5.
        """
        if rating is None:
            return False
        
        try:
            rating = int(rating)
            return 1 <= rating <= 5
        except (ValueError, TypeError):
            return False