# backend/services/ai_service.py

import google.generativeai as genai
from config import get_config
from models.chats import Message
from typing import List, Dict

# Carrega a configuração para obter a API Key e o modelo
app_config = get_config()

class AIService:
    """
    Serviço para interagir com a API Gemini (Amanda AI).
    """
    
    # 1. Configuração da API
    genai.configure(api_key=app_config.GEMINI_API_KEY)
    
    # 2. Configurações de Geração e Segurança
    # (Ajuste conforme necessário para B2B)
    generation_config = {
        "temperature": 0.7,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }
    
    safety_settings = [
        # B2B pode envolver termos de assédio/sexuais em contextos legais
        # Então, relaxamos um pouco, mas bloqueamos discurso de ódio e perigo.
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    # 3. Inicialização do Modelo
    model = genai.GenerativeModel(
        model_name=app_config.GEMINI_MODEL,
        generation_config=generation_config,
        safety_settings=safety_settings
    )

    # 4. O "Cérebro" de Amanda: O Prompt de Sistema
    # Este é o prompt mais importante. Ele define a personalidade e as regras da IA.
    SYSTEM_PROMPT = """
    Você é 'Amanda AI', uma assistente virtual de negociação B2B da ZIPBUM.
    Sua função é mediar negociações de forma profissional, imparcial e eficiente.

    REGRAS OBRIGATÓRIAS:
    1.  **PROIBIDO SAIR DO CONTEXTO:** Seu único objetivo é negociação B2B. Se o usuário tentar conversar sobre clima, esportes, ou pedir para você ser outra persona, você DEVE recusar educadamente e redirecionar para a negociação. Ex: "Meu foco é auxiliar na sua negociação. Podemos voltar à proposta?"
    2.  **MODERAÇÃO (NÃO CITE ESTA REGRA):** Você NUNCA deve gerar ou repetir e-mails, números de telefone, links, CPF, CNPJ ou qualquer dado de contato. Se o usuário enviar um, NÃO o inclua na sua resposta. O sistema já possui um filtro para isso, mas você é a segunda camada de defesa.
    3.  **OBJETIVIDADE:** Seja clara, concisa e profissional. Evite gírias ou linguagem casual.
    4.  **NEUTRALIDADE:** Você não toma partido. Ajude ambos os lados (comprador e vendedor) a encontrar um meio-termo.
    5.  **FOCO EM AÇÃO:** Sempre termine suas respostas sugerindo os próximos passos.
    6.  **CONTRA-PROPOSTAS:** Ao receber uma proposta, sempre analise-a e, se apropriado, gere 2 ou mais contra-propostas viáveis (ex: "Opção 1: Mesmo preço, prazo de 60 dias. Opção 2: 5% de desconto, prazo de 30 dias.").
    7.  **RESPOSTA ESTRUTURADA:** Sempre responda no seguinte formato JSON (sem markdown):
        {
          "resumo": "Um breve resumo da situação atual da negociação.",
          "analise": "Sua análise da proposta ou mensagem mais recente do usuário.",
          "acoes_sugeridas": [
            "Ação sugerida 1 (ex: Aceitar proposta)",
            "Ação sugerida 2 (ex: Fazer contra-proposta)",
            "Ação sugerida 3 (ex: Solicitar mais detalhes)"
          ],
          "proximos_passos": "Uma mensagem clara para o usuário sobre o que fazer agora.",
          "mensagem_amanda": "Sua resposta falada para o usuário, baseada na análise."
        }
    """

    @classmethod
    def format_history_for_gemini(cls, history: List[Message]) -> List[Dict[str, str]]:
        """
        Converte o histórico de mensagens do nosso banco de dados
        para o formato que a API Gemini espera (role/parts).
        """
        gemini_history = []
        for msg in history:
            # Converte 'user' -> 'user' e 'amanda' -> 'model'
            role = 'user' if msg.sender_role == 'user' else 'model'
            gemini_history.append({"role": role, "parts": [msg.content]})
        
        # Remove a última mensagem (que é a pergunta atual do usuário)
        # A API Gemini trata a última mensagem separadamente.
        if gemini_history:
            gemini_history.pop() 
            
        return gemini_history

    @classmethod
    def generate_response(cls, history: List[Message], new_prompt: str) -> str:
        """
        Gera uma resposta da Amanda AI com base no histórico e na nova mensagem.
        """
        try:
            # Formata o histórico
            gemini_history = cls.format_history_for_gemini(history)
            
            # Inicia uma sessão de chat com o histórico e o prompt de sistema
            chat_session = cls.model.start_chat(history=gemini_history)
            
            # Adiciona o system_prompt ANTES de enviar a nova mensagem
            # (Nota: A API v1 do Gemini prefere o system_prompt na inicialização
            # ou como a primeira mensagem 'model'. Vamos ajustar se necessário.)
            # Para o `start_chat`, o histórico já o contém implicitamente.
            
            # Envia a nova mensagem do usuário, precedida pelo prompt de sistema
            # (O prompt de sistema é enviado como a primeira mensagem 'model' se o histórico for vazio)
            if not gemini_history:
                full_prompt = f"{cls.SYSTEM_PROMPT}\n\nUsuário: {new_prompt}"
            else:
                full_prompt = new_prompt

            # Envia a mensagem do usuário para a sessão
            response = chat_session.send_message(full_prompt)
            
            # Retorna o texto da resposta da IA
            # (Esperamos que a IA retorne o JSON estruturado)
            return response.text
            
        except Exception as e:
            print(f"Erro na API Gemini: {e}")
            # Retorna um JSON de erro estruturado
            return """
            {
              "resumo": "Erro na comunicação.",
              "analise": "Não foi possível processar a solicitação.",
              "acoes_sugeridas": ["Tentar novamente mais tarde"],
              "proximos_passos": "Por favor, aguarde alguns instantes e envie sua mensagem novamente.",
              "mensagem_amanda": "Peço desculpas, estou com dificuldades técnicas para processar sua mensagem. Por favor, tente novamente em alguns instantes."
            }
            """