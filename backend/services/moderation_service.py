import re
from typing import Optional

# Importa as configurações de padrões de regex
from config import Config 

class ModeradorConteudo:
    """
    Serviço dedicado à moderação automática de conteúdo e detecção de informações
    pessoais/sensíveis (e-mail, telefone, CPF, CNPJ) em tempo real nas mensagens de chat.
    """

    def __init__(self):
        """Inicializa o moderador com os padrões de contato definidos em Config."""
        try:
            self.contact_patterns = Config.CONTACT_PATTERNS
        except AttributeError:
            # Fallback seguro caso Config.CONTACT_PATTERNS não esteja disponível
            print("⚠️ AVISO: Padrões de contato não carregados da Config. Usando padrões de segurança.")
            self.contact_patterns = {
                'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'phone': r'(\+55\s?)?(\(?\d{2}\)?[\s-]?)?\d{4,5}[\s-]?\d{4}',
                'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
                'cnpj': r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
            }

    def verificar_conteudo_proibido(self, message: str) -> Optional[str]:
        """
        Verifica se a mensagem contém qualquer padrão de contato proibido.

        Retorna:
            O nome da categoria da violação (ex: 'email', 'phone') se detectado,
            ou None se o conteúdo for seguro.
        """
        # 1. Detecção de Informações de Contato Proibidas
        for violation_type, pattern in self.contact_patterns.items():
            # A flag re.IGNORECASE garante que a detecção não seja sensível a maiúsculas/minúsculas
            if re.search(pattern, message, re.IGNORECASE):
                # Retorna o tipo de violação para que a rota possa agir (congelar, reportar)
                return violation_type
        
        # 2. (Poderia incluir aqui outras regras, como detecção de discurso de ódio/links maliciosos,
        # mas mantemos o foco nas regras de negócio de contato e LLM)
        
        return None

    def redact_message(self, message: str) -> str:
        """
        Redige (mascara) todas as ocorrências de padrões de contato em uma mensagem.
        Esta função pode ser usada para preparar o conteúdo para exibição em logs
        não-administrativos, conforme exigido.
        """
        redacted_message = message
        
        for violation_type, pattern in self.contact_patterns.items():
            # Substitui o padrão encontrado por um placeholder
            if violation_type in ['email', 'phone']:
                redacted_message = re.sub(pattern, f'[{violation_type.upper()}_REDACTED]', redacted_message)
            elif violation_type in ['cpf', 'cnpj']:
                # Substitui por um placeholder mais específico
                redacted_message = re.sub(pattern, f'[{violation_type.upper()}_MASCARADO]', redacted_message)

        # Se nenhuma redação for necessária, retorna a mensagem original
        return redacted_message

if __name__ == '__main__':
    # --- Teste da Lógica de Moderação ---
    moderador = ModeradorConteudo()
    
    testes = [
        "Olá, envie o boleto para meu email: gabriel.silva@teste.com.br", # Email
        "Me ligue no 55 11 98765-4321 ou 1123456789", # Telefone
        "Meu CPF é 123.456.789-00 e meu CNPJ é 00.000.000/0001-00.", # CPF e CNPJ
        "Qual o valor do Copo a R$8,00 se eu comprar 20?", # Seguro
        "Podemos conversar sobre política?", # Seguro (fora de escopo, mas não violação de contato)
    ]
    
    print("--- Teste de Detecção de Conteúdo Proibido ---")
    for msg in testes:
        violacao = moderador.verificar_conteudo_proibido(msg)
        print(f"Mensagem: '{msg[:40]}...' | Violação Detectada: {violacao}")

    print("\n--- Teste de Redação (Mascaramento) ---")
    msg_redacted = moderador.redact_message(testes[2])
    print(f"Original: {testes[2]}")
    print(f"Redigida: {msg_redacted}")