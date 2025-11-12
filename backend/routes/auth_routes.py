from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, Usuario, LogAuditoria
from config import Config
from utils.validators import Validadores
from datetime import datetime, timedelta
import re

auth_bp = Blueprint('auth', __name__)

# 🔒 Controle de tentativas de ativação
developer_activated = False
activation_attempts = {}

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint de login de usuário
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    remember_me = data.get('remember_me', False)

    # 🛡️ Validações básicas
    if not email or not password:
        return jsonify({'error': 'E-mail e senha são obrigatórios'}), 400
    
    if not Validadores.validar_email(email):
        return jsonify({'error': 'E-mail inválido'}), 400

    try:
        # 🔍 Buscar usuário
        usuario = Usuario.query.filter_by(email=email).first()
        
        if not usuario:
            # 📝 Log de tentativa falha
            log_auditoria = LogAuditoria(
                usuario_id=None,
                acao='login',
                modulo='auth',
                tipo_recurso='usuario',
                detalhes=f'Tentativa de login com e-mail não cadastrado: {email}',
                status='erro',
                endereco_ip=request.remote_addr,
                agente_usuario=request.user_agent.string
            )
            db.session.add(log_auditoria)
            db.session.commit()
            
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        # 🚫 Verificar conta banida
        if usuario.banido:
            log_auditoria = LogAuditoria(
                usuario_id=usuario.id,
                acao='login',
                modulo='auth',
                tipo_recurso='usuario',
                detalhes=f'Tentativa de login de conta banida. Motivo: {usuario.motivo_banimento}',
                status='erro',
                endereco_ip=request.remote_addr,
                agente_usuario=request.user_agent.string
            )
            db.session.add(log_auditoria)
            db.session.commit()
            
            return jsonify({
                'error': f'Conta suspensa. Motivo: {usuario.motivo_banimento or "Violação dos termos de uso"}'
            }), 403
        
        # ⏳ Verificar conta congelada
        if usuario.congelado_ate:
            try:
                congelado_ate = datetime.strptime(usuario.congelado_ate, '%d/%m/%Y %H:%M:%S')
                if congelado_ate > datetime.now():
                    return jsonify({
                        'error': f'Conta temporariamente suspensa até {usuario.congelado_ate}'
                    }), 403
            except ValueError:
                # 🔧 Se data inválida, remove congelamento
                usuario.congelado_ate = None
                db.session.commit()
        
        # 🔑 Verificar senha
        if not check_password_hash(usuario.senha_hash, password):
            # 📝 Log de senha incorreta
            log_auditoria = LogAuditoria(
                usuario_id=usuario.id,
                acao='login',
                modulo='auth',
                tipo_recurso='usuario',
                detalhes='Tentativa de login com senha incorreta',
                status='erro',
                endereco_ip=request.remote_addr,
                agente_usuario=request.user_agent.string
            )
            db.session.add(log_auditoria)
            db.session.commit()
            
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        # ✅ Login bem-sucedido
        login_user(usuario, remember=remember_me)
        usuario.ultimo_login = Config.get_current_timestamp()
        
        # 📝 Log de login bem-sucedido
        log_auditoria = LogAuditoria(
            usuario_id=usuario.id,
            acao='login',
            modulo='auth',
            tipo_recurso='usuario',
            detalhes=f'Login realizado com sucesso. Lembrar-me: {remember_me}',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': usuario.to_dict(),
            'message': 'Login realizado com sucesso'
        })
        
    except Exception as e:
        print(f'❌ Erro no login: {e}')
        
        # 📝 Log de erro interno
        log_auditoria = LogAuditoria(
            usuario_id=None,
            acao='login',
            modulo='auth',
            tipo_recurso='sistema',
            detalhes=f'Erro interno no login: {str(e)}',
            status='erro',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Endpoint de registro de usuário
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    access_code = data.get('access_code', '').strip()  # Código de acesso opcional
    agree_terms = data.get('agree_terms', False)

    # 🛡️ Validações
    if not all([email, password, full_name]):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    if not agree_terms:
        return jsonify({'error': 'Você deve concordar com os termos de uso'}), 400
    
    if not Validadores.validar_email(email):
        return jsonify({'error': 'E-mail inválido'}), 400
    
    valid_senha, msg_senha = Validadores.validar_senha(password)
    if not valid_senha:
        return jsonify({'error': msg_senha}), 400
    
    valid_nome, msg_nome = Validadores.validar_nome(full_name)
    if not valid_nome:
        return jsonify({'error': msg_nome}), 400

    try:
        # 🔍 Verificar se e-mail já existe
        if Usuario.query.filter_by(email=email).first():
            return jsonify({'error': 'E-mail já cadastrado'}), 400
        
        # 🎯 Definir cargo baseado no código de acesso
        cargo = 7  # Cliente Básico padrão
        cargo_especial = None
        
        if access_code:
            if access_code == Config.DEVELOPER_SECRET and not developer_activated:
                cargo = 0  # Desenvolvedor
                cargo_especial = 'Desenvolvedor'
                developer_activated = True
            elif access_code in ["JUNIOR002", "MARKETING003"]:
                cargo = 1 if access_code == "JUNIOR002" else 2
                cargo_especial = Config.get_role_name(cargo)
        
        # 👤 Criar novo usuário
        novo_usuario = Usuario(
            email=email,
            senha_hash=generate_password_hash(password),
            nome_completo=full_name,
            cargo=cargo
        )
        
        db.session.add(novo_usuario)
        db.session.flush()  # Para obter o ID sem commit
        
        # 📝 Log de registro
        log_auditoria = LogAuditoria(
            usuario_id=novo_usuario.id,
            acao='registro',
            modulo='auth',
            tipo_recurso='usuario',
            detalhes=f'Novo usuário registrado. Cargo: {Config.get_role_name(cargo)}. Código usado: {bool(access_code)}',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        response_data = {
            'success': True,
            'message': 'Conta criada com sucesso! Faça login para continuar.',
            'user_role': Config.get_role_name(cargo)
        }
        
        if cargo_especial:
            response_data['special_message'] = f'Conta promovida para {cargo_especial}!'
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f'❌ Erro no registro: {e}')
        db.session.rollback()
        
        # 📝 Log de erro no registro
        log_auditoria = LogAuditoria(
            usuario_id=None,
            acao='registro',
            modulo='auth',
            tipo_recurso='usuario',
            detalhes=f'Erro no registro: {str(e)}',
            status='erro',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Endpoint de logout
    """
    try:
        user_id = current_user.id
        logout_user()
        
        # 📝 Log de logout
        log_auditoria = LogAuditoria(
            usuario_id=user_id,
            acao='logout',
            modulo='auth',
            tipo_recurso='usuario',
            detalhes='Logout realizado com sucesso',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Logout realizado com sucesso'
        })
    except Exception as e:
        print(f'❌ Erro no logout: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """
    Obtém perfil do usuário atual
    """
    try:
        return jsonify({
            'success': True,
            'user': current_user.to_dict()
        })
    except Exception as e:
        print(f'❌ Erro ao obter perfil: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/profile/update', methods=['PUT'])
@login_required
def update_profile():
    """
    Atualiza perfil do usuário
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400

    try:
        updated = False
        changes = []
        
        # ✏️ Atualizar nome se fornecido
        if 'full_name' in data:
            nome = data['full_name'].strip()
            valid_nome, msg_nome = Validadores.validar_nome(nome)
            if not valid_nome:
                return jsonify({'error': msg_nome}), 400
            
            if nome != current_user.nome_completo:
                changes.append(f'Nome: {current_user.nome_completo} → {nome}')
                current_user.nome_completo = nome
                updated = True
        
        # 📍 Atualizar endereço se fornecido
        if 'address' in data:
            endereco = data['address'].strip()
            valid_endereco, msg_endereco = Validadores.validar_endereco(endereco)
            if not valid_endereco:
                return jsonify({'error': msg_endereco}), 400
            
            if endereco != current_user.endereco:
                changes.append('Endereço atualizado')
                current_user.endereco = endereco
                updated = True
        
        # 🗺️ Atualizar estado se fornecido
        if 'state' in data:
            estado = data['state'].strip()
            if estado and not Validadores.validar_uf(estado):
                return jsonify({'error': 'UF inválida'}), 400
            
            estado_upper = estado.upper() if estado else None
            if estado_upper != current_user.estado:
                changes.append(f'Estado: {current_user.estado or "Não informado"} → {estado_upper}')
                current_user.estado = estado_upper
                updated = True
        
        if updated:
            current_user.atualizado_em = Config.get_current_timestamp()
            
            # 📝 Log de atualização de perfil
            log_auditoria = LogAuditoria(
                usuario_id=current_user.id,
                acao='perfil_atualizado',
                modulo='auth',
                tipo_recurso='usuario',
                detalhes=f'Alterações no perfil: {", ".join(changes)}',
                status='sucesso',
                endereco_ip=request.remote_addr,
                agente_usuario=request.user_agent.string
            )
            db.session.add(log_auditoria)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Perfil atualizado com sucesso' if updated else 'Nenhuma alteração realizada',
            'user': current_user.to_dict()
        })
        
    except Exception as e:
        print(f'❌ Erro ao atualizar perfil: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/check-session', methods=['GET'])
def check_session():
    """
    Verifica se existe sessão ativa
    """
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        })
    else:
        return jsonify({
            'authenticated': False
        })

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Altera senha do usuário
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    # 🛡️ Validações
    if not all([current_password, new_password, confirm_password]):
        return jsonify({'error': 'Todos os campos de senha são obrigatórios'}), 400
    
    if new_password != confirm_password:
        return jsonify({'error': 'As novas senhas não coincidem'}), 400
    
    valid_senha, msg_senha = Validadores.validar_senha(new_password)
    if not valid_senha:
        return jsonify({'error': msg_senha}), 400
    
    try:
        # 🔑 Verificar senha atual
        if not check_password_hash(current_user.senha_hash, current_password):
            return jsonify({'error': 'Senha atual incorreta'}), 400
        
        # 🔄 Atualizar senha
        current_user.senha_hash = generate_password_hash(new_password)
        current_user.atualizado_em = Config.get_current_timestamp()
        
        # 📝 Log de alteração de senha
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='senha_alterada',
            modulo='auth',
            tipo_recurso='usuario',
            detalhes='Senha alterada com sucesso',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Senha alterada com sucesso'
        })
        
    except Exception as e:
        print(f'❌ Erro ao alterar senha: {e}')
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

print("✅ Auth routes carregadas com sucesso!")