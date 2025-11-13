# backend/routes/admin.py

from flask import request, jsonify
from . import admin_bp # Importa o Blueprint
from models.users import User, Role
from models.companies import Company
from models.reports import Report
from services.role_service import RoleService, roles_required
from utils.constants import Cargos
from app import db

# Níveis de permissão de Admin (ZIPBUM)
ADMIN_LEVELS = [Cargos.ADMIN_ZIPBUM, Cargos.HELPER_N1, Cargos.HELPER_N2, Cargos.HELPER_N3]

@admin_bp.route('/users', methods=['GET'])
@roles_required(ADMIN_LEVELS) # Protegido!
def get_all_users():
    """
    (Admin) Retorna uma lista de todos os utilizadores no sistema.
    """
    try:
        users = User.query.all()
        # Usamos o .to_dict() que definimos no modelo User
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        print(f"Erro ao buscar utilizadores: {e}")
        return jsonify({"error": "Erro interno ao buscar utilizadores."}), 500

@admin_bp.route('/companies', methods=['GET'])
@roles_required(ADMIN_LEVELS) # Protegido!
def get_all_companies():
    """
    (Admin) Retorna uma lista de todas as empresas registadas.
    """
    try:
        companies = Company.query.all()
        return jsonify([company.to_dict() for company in companies]), 200
    except Exception as e:
        print(f"Erro ao buscar empresas: {e}")
        return jsonify({"error": "Erro interno ao buscar empresas."}), 500

@admin_bp.route('/user/changerole', methods=['POST'])
@roles_required([Cargos.ADMIN_ZIPBUM]) # Apenas Admin Nível 0 pode mudar cargos
def change_user_role():
    """
    (Admin) Altera o cargo (nível de permissão) de um utilizador.
    """
    data = request.json
    user_id = data.get('user_id')
    new_role_level = data.get('new_role_level') # Espera um NÍVEL (0-7)

    if not user_id or new_role_level is None:
        return jsonify({"error": "user_id e new_role_level são obrigatórios."}), 400

    try:
        success = RoleService.change_user_role_by_level(user_id, int(new_role_level))
        
        if success:
            # (Futuro) Registar no AuditLog
            return jsonify({"message": f"Cargo do utilizador {user_id} alterado com sucesso."}), 200
        else:
            return jsonify({"error": "Não foi possível alterar o cargo. Utilizador ou cargo não encontrado."}), 404
            
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao mudar cargo: {e}")
        return jsonify({"error": "Erro interno ao mudar cargo."}), 500

@admin_bp.route('/reports', methods=['GET'])
@roles_required(ADMIN_LEVELS)
def get_pending_reports():
    """
    (Admin) Retorna todas as denúncias com estado 'pending'.
    """
    try:
        # Busca denúncias pendentes, das mais antigas para as mais novas
        reports = Report.query.filter_by(status='pending').order_by(Report.created_at.asc()).all()
        
        # (Idealmente, .to_dict() deveria ser definido no modelo Report)
        report_list = [{
            "report_id": r.id,
            "reporter_id": r.reporter_id,
            "reported_user_id": r.reported_user_id,
            "category": r.category,
            "description": r.description,
            "created_at": r.created_at.isoformat()
        } for r in reports]
        
        return jsonify(report_list), 200
        
    except Exception as e:
        print(f"Erro ao buscar denúncias: {e}")
        return jsonify({"error": "Erro interno ao buscar denúncias."}), 500