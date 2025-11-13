# backend/utils/constants.py

# Níveis de Permissão (Roles)
# Conforme especificado no prompt, de 0 a 7
class Cargos:
    ADMIN_ZIPBUM = 0
    HELPER_N1 = 1
    HELPER_N2 = 2
    HELPER_N3 = 3
    REPRESENTANTE = 4
    VENDEDOR = 5
    BLOQUEADO = 6
    DEVELOPER = 7

# Mapeamento de Nível para Nome
CARGOS_NOMES = {
    Cargos.ADMIN_ZIPBUM: "Admin ZIPBUM",
    Cargos.HELPER_N1: "Helper Nível 1",
    Cargos.HELPER_N2: "Helper Nível 2",
    Cargos.HELPER_N3: "Helper Nível 3",
    Cargos.REPRESENTANTE: "Representante",
    Cargos.VENDEDOR: "Vendedor",
    Cargos.BLOQUEADO: "Bloqueado",
    Cargos.DEVELOPER: "Developer"
}

# Constantes de Negociação
class StatusNegociacao:
    ATIVA = "active"
    FECHADA_SUCESSO = "closed_success"
    FECHADA_FALHA = "closed_fail"
    DENUNCIADA = "reported"

# Constantes de Proposta
class StatusProposta:
    ENVIADA = "sent"
    VISUALIZADA = "viewed"
    ACEITA = "accepted"
    REJEITADA = "rejected"
    RETIRADA = "retracted"

# Constantes de Moderação e Denúncia
CATEGORIAS_DENUNCIA = [
    'spam',
    'abuso_verbal',
    'troca_de_contato', # (email, telefone, etc.)
    'tentativa_de_fraude',
    'fora_de_contexto',
    'outro'
]

class StatusDenuncia:
    PENDENTE = "pending"
    RESOLVIDA = "resolved"
    IGNORADA = "dismissed"

# Constantes da Amanda AI
class SenderRoles:
    USER = "user"
    AMANDA = "amanda" # Ou "model" / "ia"