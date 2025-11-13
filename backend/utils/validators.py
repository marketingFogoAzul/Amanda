# backend/utils/validators.py
import re

# Regex simples para validação de e-mail (pode ser mais complexo)
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def validate_email(email: str) -> bool:
    """Verifica se um formato de e-mail é válido."""
    if not email:
        return False
    return re.match(EMAIL_REGEX, email) is not None

def validate_password_strength(password: str) -> bool:
    """
    Verifica a força da senha.
    Requisitos: Mínimo 8 caracteres, 1 maiúscula, 1 minúscula, 1 número.
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    # (Opcional) Verificar caractere especial
    # if not re.search(r'[\W_]', password):
    #     return False
    return True

def clean_cnpj(cnpj: str) -> str:
    """Remove pontuação de um CNPJ, deixando apenas dígitos."""
    return re.sub(r'[^0-9]', '', cnpj)

def format_cnpj(cnpj: str) -> str:
    """Formata um CNPJ com 14 dígitos para 00.000.000/0000-00."""
    cnpj_limpo = clean_cnpj(cnpj)
    if len(cnpj_limpo) != 14:
        return cnpj # Retorna o original se não tiver 14 dígitos
    return f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:]}"

def validate_cnpj(cnpj: str) -> bool:
    """
    Valida um CNPJ (incluindo dígitos verificadores).
    """
    cnpj_limpo = clean_cnpj(cnpj)
    
    # CNPJs com todos os dígitos iguais são inválidos
    if len(cnpj_limpo) != 14 or len(set(cnpj_limpo)) == 1:
        return False

    def calcular_dv(cnpj_parcial, pesos):
        soma = sum(int(digito) * peso for digito, peso in zip(cnpj_parcial, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    # Cálculo do primeiro dígito verificador
    pesos_dv1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dv1 = calcular_dv(cnpj_limpo[:12], pesos_dv1)
    
    if int(cnpj_limpo[12]) != dv1:
        return False

    # Cálculo do segundo dígito verificador
    pesos_dv2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dv2 = calcular_dv(cnpj_limpo[:13], pesos_dv2)
    
    return int(cnpj_limpo[13]) == dv2

# --- Exemplo de uso (não faz parte do arquivo) ---
# if __name__ == "__main__":
#     test_cnpj = "00.000.000/0001-91" # CNPJ válido (Receita Federal)
#     print(f"CNPJ: {test_cnpj}")
#     print(f"Limpo: {clean_cnpj(test_cnpj)}")
#     print(f"Válido: {validate_cnpj(test_cnpj)}")
#     print(f"Formatado: {format_cnpj('00000000000191')}")