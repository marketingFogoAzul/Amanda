# backend/routes/auth.py

from flask import request, jsonify
from . import auth_bp # Importa o Blueprint
from models.users import User, Role
from models.companies import Company
from utils.validators import validate_email, validate_password_strength, validate_cnpj, format_cnpj, clean_cnpj
from utils.security import hash_password, check_password, create_access_token
from utils.constants import Cargos
from config import get_config
from app import db
import requests # Para verificar o reCAPTCHA
import uuid

# Carrega a configuração para chaves (reCAPTCHA, Dev Code)
app_config = get_config()

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Endpoint de Registro de novas empresas e usuários (Representantes).
    """
    data = request.json
    
    # 1. Validação de Dados Básicos
    required_fields = ['full_name', 'email', 'password', 'cnpj', 'razao_social', 'uf', 'recaptcha_token']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Dados incompletos."}), 400

    email = data.get('email').lower().strip()
    password = data.get('password')
    cnpj = data.get('cnpj')
    
    # 2. Verificação do reCAPTCHA
    recaptcha_secret = app_config.RECAPTCHA_SECRET_KEY
    recaptcha_token = data.get('recaptcha_token')
    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={'secret': recaptcha_secret, 'response': recaptcha_token}
    )
    recaptcha_result = response.json()
    if not recaptcha_result.get('success') or recaptcha_result.get('score', 0) < 0.5:
        return jsonify({"error": "Falha na verificação do reCAPTCHA."}), 401

    # 3. Validação de Regras de Negócio
    if not validate_email(email):
        return jsonify({"error": "Formato de e-mail inválido."}), 400
        
    if not validate_password_strength(password):
        return jsonify({"error": "Senha fraca. Use 8+ caracteres, maiúscula, minúscula e número."}), 400
        
    if not validate_cnpj(cnpj):
        return jsonify({"error": "CNPJ inválido."}), 400

    # 4. Verificação de Duplicidade
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Este e-mail já está em uso."}), 409
        
    cnpj_limpo = clean_cnpj(cnpj)
    if Company.query.filter_by(cnpj=format_cnpj(cnpj_limpo)).first():
        return jsonify({"error": "Este CNPJ já está cadastrado."}), 409

    # 5. Lógica de Criação
    try:
        # Cria a Empresa
        company_id = str(uuid.uuid4())
        new_company = Company(
            id=company_id,
            cnpj=format_cnpj(cnpj_limpo),
            razao_social=data.get('razao_social'),
            uf=data.get('uf').upper(),
            nome_fantasia=data.get('nome_fantasia'),
            cidade=data.get('cidade')
        )
        db.session.add(new_company)
        
        # Define o cargo do usuário
        # O primeiro usuário é sempre "Representante" (Nível 4)
        role_level = Cargos.REPRESENTANTE
        
        # CÓDIGO SECRETO DEV (Qazxcvbnmlp7@)
        # Se o código secreto for enviado no campo 'password',
        # e o email for de admin, cria um usuário Developer (Nível 7)
        if password == app_config.DEV_SECRET_CODE and "admin@zipbum" in email:
            role_level = Cargos.DEVELOPER
        
        role = Role.query.filter_by(permission_level=role_level).first()
        if not role:
            return jsonify({"error": f"Cargo de nível {role_level} não encontrado no banco."}), 500

        # Cria o Usuário
        new_user = User(
            id=str(uuid.uuid4()),
            full_name=data.get('full_name'),
            email=email,
            password=password, # O hash é feito no __init__ do User
            role_id=role.id,
            company_id=company_id
        )
        db.session.add(new_user)
        
        # Confirma as transações
        db.session.commit()

        return jsonify({"message": "Empresa e usuário registrados com sucesso!"}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Erro no registro: {e}")
        return jsonify({"error": "Erro interno ao processar o registro."}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint de Login. Retorna um token JWT.
    """
    data = request.json
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"error": "E-mail e senha são obrigatórios."}), 400

    try:
        user = User.query.filter_by(email=email).first()

        # Verifica se o usuário existe E a senha está correta
        if not user or not user.check_password(password):
            return jsonify({"error": "Credenciais inválidas."}), 401
            
        # Verifica se o usuário está ativo (não bloqueado)
        if not user.is_active or user.is_blocked:
            # (Opcional) Verificar se o bloqueio expirou
            if user.blocked_until and user.blocked_until > DateService.get_now():
                return jsonify({"error": f"Usuário bloqueado até {DateService.format_date(user.blocked_until)}."}), 403
            else:
                # Libera o usuário se o tempo de bloqueio passou
                user.is_blocked = False
                user.blocked_until = None
                db.session.commit()

        # Se passou, cria o token
        # O token é criado usando o *objeto* 'user'
        # O callback @jwt.user_identity_loader (em security.py) usa o user.id
        # O callback @jwt.additional_claims_loader (em security.py) usa o user.role
        access_token = create_access_token(identity=user)
        
        return jsonify(
            access_token=access_token,
            user=user.to_dict() # Envia os dados do usuário para o frontend
        ), 200

    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify({"error": "Erro interno no servidor."}), 500