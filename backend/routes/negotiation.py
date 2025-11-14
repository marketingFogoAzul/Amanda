# backend/routes/negotiation.py

from flask import request, jsonify
from . import negotiation_bp # Importa o Blueprint
from models.users import User
from models.negotiations import Negotiation, Proposal
from utils.security import jwt_required, get_user_identity
from utils.constants import StatusProposta
from app import db
import uuid
import json

@negotiation_bp.route('/proposal/create', methods=['POST'])
@jwt_required()
def create_proposal():
    """
    Cria uma nova Proposta formal numa Negociação.
    """
    user_id = get_user_identity()
    data = request.json
    
    negotiation_id = data.get('negotiation_id')
    details_json = data.get('details') # O frontend envia um objeto JSON
    total_value = data.get('total_value')

    if not negotiation_id or not details_json or not total_value:
        return jsonify({"error": "negotiation_id, details (JSON) e total_value são obrigatórios."}), 400
        
    # Verifica se a negociação existe
    neg = Negotiation.query.get(negotiation_id)
    if not neg:
        return jsonify({"error": "Negociação não encontrada."}), 404
        
    # (Validação futura: verificar se o user_id pertence à negociação)

    try:
        new_proposal = Proposal(
            id=str(uuid.uuid4()),
            negotiation_id=negotiation_id,
            proposer_user_id=user_id,
            # Converte o objeto JSON (dict) para uma string JSON
            details_json=json.dumps(details_json),
            total_value=float(total_value),
            status=StatusProposta.ENVIADA
        )
        db.session.add(new_proposal)
        db.session.commit()
        
        return jsonify({"message": "Proposta enviada com sucesso!", "proposal_id": new_proposal.id}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar proposta: {e}")
        return jsonify({"error": "Erro interno ao criar proposta."}), 500

@negotiation_bp.route('/proposal/<string:proposal_id>/<string:action>', methods=['POST'])
@jwt_required()
def action_on_proposal(proposal_id, action):
    """
    Executa uma ação (aceitar ou rejeitar) numa proposta.
    Ação = 'accept' ou 'reject'
    """
    user_id = get_user_identity()
    
    proposal = Proposal.query.get(proposal_id)
    if not proposal:
        return jsonify({"error": "Proposta não encontrada."}), 404
        
    # (Validação futura: verificar se o user_id é o destinatário da proposta)
    
    try:
        if action == 'accept':
            proposal.status = StatusProposta.ACEITA
            # (Opcional) Mudar o status da Negociação principal
            # proposal.negotiation.status = StatusNegociacao.FECHADA_SUCESSO
            message = "Proposta aceite com sucesso."
            
        elif action == 'reject':
            proposal.status = StatusProposta.REJEITADA
            message = "Proposta rejeitada."
            
        else:
            return jsonify({"error": "Ação inválida. Use 'accept' ou 'reject'."}), 400

        db.session.commit()
        return jsonify({"message": message, "proposal_status": proposal.status}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Erro na ação da proposta: {e}")
        return jsonify({"error": "Erro interno ao processar a ação."}), 500