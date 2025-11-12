import os
import json
import random
from typing import List, Dict, Any, Union, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from config import Config

# --- Definição de Estrutura de Resposta do Gemini (JSON Schema) ---
# Usamos um esquema JSON para garantir que o modelo Gemini retorne
# uma resposta estruturada e determinística, como exigido.

NEGOTIATION_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "resumo_curto": {
            "type": "string",
            "description": "Um resumo conciso de 1-2 linhas sobre o status atual da negociação ou a resposta imediata."
        },
        "ofertas": {
            "type": "array",
            "description": "Lista de no mínimo 2 contra-ofertas (calculadas proceduralmente) mais a condição de preço final.",
            "items": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["contra_oferta", "oferta_final", "informativo"]},
                    "titulo": {"type": "string", "description": "Ex: Opção 1: 24 unid. @ R$8,80"},
                    "condicoes": {"type": "string", "description": "Condições aplicadas (Preço, Quantidade Mínima, Total)." }
                },
                "required": ["tipo", "titulo", "condicoes"]
            }
        },
        "acoes_sugeridas": {
            "type": "array",
            "description": "Lista de ações que o usuário pode clicar (botões). Não deve ter mais de 3 itens.",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "description": "Texto do botão (Ex: 'Aceitar Opção 2', 'Solicitar Ajuda Humana')"},
                    "acao_tipo": {"type": "string", "description": "Tipo de ação interna (Ex: 'confirm_offer_2', 'handoff')"}
                },
                "required": ["label", "acao_tipo"]
            }
        },
        "proximos_passos": {
            "type": "string",
            "description": "Sugestão de próximo input ou passo necessário para o usuário avançar."
        },
        "fora_de_escopo": {
            "type": "boolean",
            "description": "True se a mensagem do usuário for irrelevante ou fora do escopo (política, clima, papo casual). Se True, a resposta deve focar em redirecionamento."
        }
    },
    "required": ["resumo_curto", "acoes_sugeridas", "proximos_passos", "fora_de_escopo", "ofertas"]
}

# --- Mock de Estrutura de Descontos por Volume (Simula a Planilha Importada) ---
# A estrutura deve conter todos os níveis de preço.
MOCK_PRODUCT_DISCOUNTS = {
    # Usaremos um produto fictício aqui, mas em produção este dicionário seria preenchido
    # pelos dados lidos da sua planilha de regras (Pasta1.xlsx)
    "copo": [
        (1, 10.00),     # Nível 0: Preço Base
        (10, 9.00),     # Nível 1
        (20, 8.00),     # Nível 2: Preço Alvo do Cliente (Ex: R$8,00)
        (30, 7.00),     # Nível 3
        (40, 6.00),
        (50, 5.00),
    ]
}

class NegociadorAmanda:
    """
    Serviço de IA para Negociação.
    Encapsula a lógica de interação com o modelo Gemini para garantir o cumprimento
    das regras de negócio da Amanda AI e da plataforma ZIPBUM.
    """

    def __init__(self):
        """Inicializa o cliente Gemini."""
        self.model = 'gemini-2.5-flash'
        # ✅ CORREÇÃO: Usa o módulo 'genai' configurado globalmente em app.py
        self.client = genai 

    def _get_system_prompt(self, calculated_offers: List[Dict[str, Any]]) -> str:
        """
        Retorna o Prompt do Sistema completo com as regras e INJETANDO as ofertas calculadas.
        """
        offers_str = json.dumps(calculated_offers, ensure_ascii=False)
        
        prompt = f"""
        Você é a Amanda AI, assistente de negociação exclusiva da plataforma B2B ZIPBUM.
        Seu único propósito é auxiliar, automatizar e gerenciar negociações.

        --- IDENTIDADE E TOM ---
        - Profissional, concisa, focada, procedural.
        - Use sempre Português do Brasil. Se o usuário estiver fora de escopo, defina 'fora_de_escopo': true.

        --- REGRAS DE NEGÓCIO ---
        1. **Resposta Estruturada:** Você DEVE responder estritamente no formato JSON fornecido.
        2. **Contra-Ofertas:** As propostas de negociação já foram calculadas proceduralmente (por uma função de negócio)
           e estão INJETADAS abaixo. Seu trabalho é INTEGRAR estas ofertas no campo 'ofertas' do JSON
           e garantir que o 'resumo_curto' e 'proximos_passos' as referenciem de forma profissional.
           O campo 'ofertas' no JSON de saída DEVE ser EXATAMENTE IGUAL ao conteúdo injetado.

        --- OFERTAS CALCULADAS PARA INTEGRAÇÃO ---
        {offers_str}
        """
        return prompt

    def _format_chat_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Formata o histórico do chat da estrutura do banco de dados para o formato do Gemini API.
        """
        formatted_history = []
        for msg in history:
            role = 'user' if msg['tipo_remetente'] == 'usuario' else 'model'
            if msg.get('removida') or msg['tipo_remetente'] == 'sistema':
                 continue
            formatted_history.append({
                "role": role,
                "parts": [{"text": msg['conteudo']}]
            })
        return formatted_history

    def _extract_negotiation_request(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Tenta extrair Produto, Quantidade e Preço de uma mensagem de usuário.
        Esta simulação é genérica. Em um sistema real, usaria modelos NLP mais complexos.
        """
        # Exemplo de parsing simplificado (Assumindo que o cliente está negociando 'copo')
        if "copo" in message.lower():
             # MOCK: Assume que o preço alvo do cliente é o Nível 2 do desconto (20 unidades @ R$8.00)
            return {
                "produto": "Copo",
                "quantidade": 20,
                "preco_proposto": 8.00 # Preço alvo do cliente
            }
        return None
    
    def _calculate_counter_offers(self, product_name: str, requested_qty: int, target_price: float) -> List[Dict[str, Any]]:
        """
        Lógica Determinística: Calcula 2 contra-ofertas intermediárias + Oferta Final.
        Garante QTD >= solicitada e PREÇO decrescente em direção ao alvo.
        """
        discounts = self._get_product_discount_data(product_name)
        if not discounts:
            # Fallback para negociação padrão se não houver dados de desconto
            return []

        # 1. Obter Preço Base e Definir Quantidade (QTD >= solicitada)
        base_price = discounts[0][1] # Ex: 10.00
        # Usamos 4 unidades a mais (4 é um passo arbitrário para negociação por volume)
        FINAL_QTY = requested_qty + 4 # Ex: 20 + 4 = 24
        
        # 2. Calcular o range de negociação disponível
        # Assume que o cliente já encontrou o preço alvo (target_price) para a QTD solicitada (20)
        total_discount_range = base_price - target_price # Ex: 10.00 - 8.00 = 2.00

        # 3. Definir os Passos de Preço
        # O preço deve descer do Base (10.00) até o Target (8.00) em 3 passos lógicos.
        
        # Preço 1 (Menos agressivo): 40% do range de desconto total A PARTIR do preço base.
        price_1 = base_price - (total_discount_range * 0.40) # Ex: 10.00 - (2.00 * 0.40) = 9.20
        
        # Preço 2 (Mais agressivo): 60% do range de desconto total A PARTIR do preço base.
        price_2 = base_price - (total_discount_range * 0.60) # Ex: 10.00 - (2.00 * 0.60) = 8.80
        
        # 4. Construir Ofertas
        ofertas = [
            {
                "tipo": "contra_oferta",
                "titulo": f"Opção 1: {FINAL_QTY} unid. @ R${price_1:.2f} (Total: R${round(FINAL_QTY * price_1, 2):.2f})",
                "condicoes": f"Valor unitário com {round(total_discount_range * 0.40 * 100 / base_price, 1)}% de desconto. Quantidade mínima {FINAL_QTY} unid. (Entrega Imediata)"
            },
            {
                "tipo": "contra_oferta",
                "titulo": f"Opção 2: {FINAL_QTY} unid. @ R${price_2:.2f} (Total: R${round(FINAL_QTY * price_2, 2):.2f})",
                "condicoes": f"Valor unitário com {round(total_discount_range * 0.60 * 100 / base_price, 1)}% de desconto. Quantidade mínima {FINAL_QTY} unid. (Frete Grátis)"
            },
            {
                "tipo": "oferta_final",
                "titulo": f"Oferta Final (Se aceita agora): {requested_qty} unid. @ R${target_price:.2f} (Total: R${round(requested_qty * target_price, 2):.2f})",
                "condicoes": f"Preço de desconto por volume (Tier {requested_qty}) liberado para a quantidade solicitada."
            }
        ]
        
        return ofertas

    def _get_product_discount_data(self, product_name: str) -> List[tuple]:
        """
        MOCK: Simula a busca no banco de dados para a estrutura de descontos do produto.
        """
        product_key = product_name.lower().split()[0]
        # Em produção, esta função leria do banco de dados, filtrando a regra
        # pelo produto e retornando os 5 pares (qtd, preco).
        return MOCK_PRODUCT_DISCOUNTS.get(product_key, [])

    def gerar_resposta_negociacao(self, new_message: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gera uma resposta estruturada da Amanda AI para uma nova mensagem.
        """
        # 1. Tentar extrair intenção de negociação
        neg_request = self._extract_negotiation_request(new_message)
        calculated_offers = []
        
        if neg_request:
            # 2. Se houver, calcular ofertas deterministicamente
            calculated_offers = self._calculate_counter_offers(
                neg_request['produto'], 
                neg_request['quantidade'], 
                neg_request['preco_proposto']
            )

        try:
            safety_settings = [
                {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
            ]

            formatted_history = self._format_chat_history(history)
            
            # Adicionar a nova mensagem
            formatted_history.append({
                "role": "user",
                "parts": [{"text": new_message}]
            })

            # Chamar o modelo com as ofertas INJETADAS no System Prompt
            response = self.client.models.generate_content(
                model=self.model,
                contents=formatted_history,
                config={
                    "system_instruction": self._get_system_prompt(calculated_offers),
                    "response_mime_type": "application/json",
                    "response_schema": NEGOTIATION_RESPONSE_SCHEMA,
                    "safety_settings": safety_settings,
                    "temperature": 0.2
                }
            )

            # Processar e retornar a resposta
            resposta_json = json.loads(response.text)
            
            # Garantir que as ofertas calculadas proceduralmente NÃO sejam perdidas
            if calculated_offers and not resposta_json.get('ofertas'):
                resposta_json['ofertas'] = calculated_offers
            elif calculated_offers:
                # Se o LLM tentar gerar, garantimos que o LLM só formatou
                # Mas para a rota chat_routes, precisamos de 'conteudo' e 'acoes'
                pass 
                
            return {
                'conteudo': resposta_json['resumo_curto'],
                'acoes': resposta_json['acoes_sugeridas'],
                'ofertas': resposta_json['ofertas'], # Inclui as ofertas para a rota
                'proximos_passos': resposta_json['proximos_passos'],
                'fora_de_escopo': resposta_json['fora_de_escopo']
            }

        except Exception as e:
            print(f"❌ Erro na chamada Gemini: {e}")
            # Resposta de fallback em caso de erro
            return {
                'conteudo': "Desculpe, estou com dificuldades técnicas. Tente novamente mais tarde ou clique em 'Solicitar Suporte'.",
                'acoes': [
                    {'label': 'Nova Negociação', 'acao_tipo': 'start_new'},
                    {'label': 'Solicitar Suporte', 'acao_tipo': 'request_support'}
                ],
                'ofertas': [],
                'proximos_passos': 'Aguarde um momento e refaça sua pergunta, ou solicite suporte.',
                'fora_de_escopo': False
            }

    def gerar_retomada_inatividade(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gera uma mensagem de resumo e retomada do chat após 10 minutos de inatividade
        por parte do atendente humano. (Lógica mantida da versão anterior)
        """
        ultima_interacao = "Nenhuma interação recente."
        for msg in reversed(history):
            if msg['tipo_remetente'] in ['usuario', 'humano']:
                ultima_interacao = msg['conteudo']
                break

        resumo_inativ = f"O atendente humano está inativo há mais de 10 minutos. Retomarei o controle. A última mensagem foi: '{ultima_interacao[:60]}...'. Deseja continuar a negociação ou prefere aguardar?"
        
        return {
            'conteudo': resumo_inativ,
            'acoes': [
                {'label': 'Continuar Negociação com Amanda', 'acao_tipo': 'continue_ai'},
                {'label': 'Aguardar Atendente', 'acao_tipo': 'wait_human'}
            ],
            'ofertas': [],
            'proximos_passos': 'Por favor, selecione uma das opções acima para darmos continuidade.',
            'fora_de_escopo': False
        }