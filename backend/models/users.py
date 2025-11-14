import datetime
from sqlalchemy.sql import func # Para timestamps automáticos
from app import db, bcrypt # Importa 'db' e 'bcrypt' do app.py

class Role(db.Model):
    """
    Modelo para os Cargos/Funções (Níveis de permissão).
    0 = Admin ZIPBUM
    1 = Helper Nível 1
    2 = Helper Nível 2
    3 = Helper Nível 3
    4 = Representante (Empresa)
    5 = Vendedor (Empresa)
    6 = Usuário Bloqueado
    7 = Developer (Acesso especial)
    """
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    # Nível de permissão, 0-7
    permission_level = db.Column(db.Integer, unique=True, nullable=False)
    
    # Relação inversa: um cargo pode ter muitos usuários
    users = db.relationship('User', back_populates='role')

    def __repr__(self):
        return f'<Role {self.name} (Level {self.permission_level})>'

class User(db.Model):
    """
    Modelo para Usuários da plataforma.
    """
    __tablename__ = 'users'
    
    # Usamos String(36) para armazenar um UUID (como string)
    id = db.Column(db.String(36), primary_key=True) 
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Chaves Estrangeiras
    # Opcional para admins (nullable=True)
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=True) 
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_blocked = db.Column(db.Boolean, default=False, nullable=False)
    blocked_until = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    
    # Relações (linking)
    # 'company' e 'role' nos dão acesso aos objetos completos
    company = db.relationship('Company', back_populates='users')
    role = db.relationship('Role', back_populates='users')
    
    # --- CORREÇÃO AQUI ---
    # Relações com outras tabelas (agora descomentadas e indentadas)
    chats = db.relationship('Chat', back_populates='user')
    reports_made = db.relationship('Report', foreign_keys='Report.reporter_id', back_populates='reporter')
    reports_received = db.relationship('Report', foreign_keys='Report.reported_user_id', back_populates='reported_user')
    audit_logs = db.relationship('AuditLog', back_populates='user')
    evaluations = db.relationship('Evaluation', back_populates='user')
    # ---------------------

    def __init__(self, id, full_name, email, password, role_id, company_id=None):
        self.id = id
        self.full_name = full_name
        self.email = email
        # Chama a função set_password para gerar o hash
        self.set_password(password)
        self.role_id = role_id
        self.company_id = company_id

    def set_password(self, password):
        """Cria um hash seguro da senha."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verifica se a senha fornecida bate com o hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Retorna um dicionário serializável do usuário (sem a senha)."""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'company_id': self.company_id,
            'role': self.role.name if self.role else None,
            'role_level': self.role.permission_level if self.role else None,
            'is_active': self.is_active,
            'is_blocked': self.is_blocked,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.email} (ID: {self.id})>'