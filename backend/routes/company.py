# backend/routes/company.py

from flask import request, jsonify
from . import company_bp # Importa o Blueprint
from models.users import User, Role
from models.companies import Company
from utils.security import jwt_required, get_user_identity
from services.role_service import roles_required
from utils.constants import Cargos
from utils.validators import validate_email, validate_password_strength
from app import db
import uuid

# Apenas Representantes (Nível 4) podem gerir a equipa
COMPANY_ADMIN_LEVELS = [Cargos.REPRESENTANTE]

@company_bp.route('/team', methods=['GET'])
@roles_required(COMPANY_ADMIN_LEVELS + [Cargos.VENDEDOR]) # Representante ou Vendedor
def get_company_team():
    """
    (Empresa) Retorna todos os utilizadores (Vendedores e Representantes)
    associados à empresa do utilizador logado.
    """
    user_id = get_user_identity()
    user = User.query.get(user_id)
    
    if not user or not user.company_id:
        return jsonify({"error": "Utilizador não está associado a uma empresa."}), 404
        
    try:
        team_members = User.query.filter_by(company_id=user.company_id).all()
        return jsonify([member.to_dict() for member in team_members]), 200
        
    except Exception as e:
        print(f"Erro ao buscar equipa: {e}")
        return jsonify({"error": "Erro interno ao buscar equipa."}), 500

@company_bp.route('/add_seller', methods=['POST'])
@roles_required(COMPANY_ADMIN_LEVELS) # Apenas Representante pode adicionar
def add_seller_to_team():
    """
    (Representante) Adiciona um novo Vendedor (Nível 5) à sua empresa.
    """
    user_id = get_user_identity()
    user = User.query.get(user_id) # Este é o Representante
    
    if not user or not user.company_id:
        return jsonify({"error": "Apenas representantes de empresa podem adicionar vendedores."}), 403

    data = request.json
    email = data.get('email', '').lower().strip()
    password = data.get('password')
    full_name = data.get('full_name')

    # Validações
    if not validate_email(email):
        return jsonify({"error": "Formato de e-mail inválido."}), 400
    if not validate_password_strength(password):
        return jsonify({"error": "Senha fraca. Use 8+ caracteres, maiúscula, minúscula e número."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Este e-mail já está em uso."}), 409

    try:
        # Busca o cargo "Vendedor" (Nível 5)
        seller_role = Role.query.filter_by(permission_level=Cargos.VENDEDOR).first()
        if not seller_role:
            return jsonify({"error": "Cargo de Vendedor não encontrado no sistema."}), 500
            
        # Cria o novo utilizador (Vendedor)
        new_seller = User(
            id=str(uuid.uuid4()),
            full_name=full_name,
            email=email,
            password=password, # Hash é feito no __init__
            role_id=seller_role.id,
            company_id=user.company_id # Vincula à empresa do Representante
        )
        db.session.add(new_seller)
        db.session.commit()
        
        return jsonify({
            "message": "Vendedor adicionado com sucesso!",
            "user": new_seller.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao adicionar vendedor: {e}")
        return jsonify({"error": "Erro interno ao adicionar vendedor."}), 500