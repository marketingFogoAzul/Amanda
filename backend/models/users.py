from . import db
from flask_login import UserMixin
from config import Config
from datetime import datetime

class Usuario(UserMixin, db.Model):
    """
    Modelo de Usuário - Sistema completo de autenticação e cargos
    """
    
    __tablename__ = 'usuarios'
    
    # 🔑 Identificação
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    nome_completo = db.Column(db.String(200), nullable=False)
    
    # 👥 Cargo e Empresa
    cargo = db.Column(db.Integer, default=7, nullable=False)  # Padrão: Cliente Básico
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'))
    
    # 📍 Localização
    endereco = db.Column(db.String(300))
    estado = db.Column(db.String(2))  # UF
    
    # 🔒 Status da Conta
    ativo = db.Column(db.Boolean, default=True)
    banido = db.Column(db.Boolean, default=False)
    motivo_banimento = db.Column(db.Text)
    congelado_ate = db.Column(db.String(20))  # Timestamp no formato DD/MM/YYYY HH:MM:SS
    
    # ⏰ Timestamps
    criado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    ultimo_login = db.Column(db.String(20))
    atualizado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    
    # 🔗 Relacionamentos
    empresa = db.relationship('Empresa', back_populates='usuarios')
    chats = db.relationship('Chat', back_populates='usuario', foreign_keys='Chat.usuario_id')
    chats_assumidos = db.relationship('Chat', back_populates='assumido_por', foreign_keys='Chat.assumido_por_id')
    relatorios_feitos = db.relationship('Relatorio', back_populates='relator', foreign_keys='Relatorio.relator_id')
    avisos_criados = db.relationship('AvisoEmpresa', back_populates='autor', foreign_keys='AvisoEmpresa.criado_por_id')
    logs_importacao = db.relationship('LogImportacao', back_populates='usuario')
    
    def get_nome_cargo(self):
        """Retorna o nome do cargo"""
        return Config.get_role_name(self.cargo)
    
    def pode_atribuir_cargos(self):
        """Verifica se pode atribuir cargos a outros usuários"""
        return Config.can_assign_roles(self.cargo)
    
    def pode_gerenciar_empresa(self):
        """Verifica se pode gerenciar painel empresarial"""
        return Config.can_manage_company(self.cargo)
    
    def eh_admin(self):
        """Verifica se é cargo administrativo"""
        return Config.is_admin(self.cargo)
    
    def eh_usuario_empresa(self):
        """Verifica se é usuário de empresa (Representante/Vendedor)"""
        return Config.is_company_user(self.cargo)
    
    def eh_cliente(self):
        """Verifica se é cliente"""
        return Config.is_client(self.cargo)
    
    def esta_congelado(self):
        """Verifica se a conta está congelada"""
        if not self.congelado_ate:
            return False
        
        try:
            congelado_ate = datetime.strptime(self.congelado_ate, '%d/%m/%Y %H:%M:%S')
            return congelado_ate > datetime.now()
        except ValueError:
            # Se data inválida, remove congelamento
            self.congelado_ate = None
            db.session.commit()
            return False
    
    def pode_fazer_upload(self):
        """Verifica se pode fazer upload de planilhas"""
        return self.cargo in [0, 1, 2, 3]  # Dev, Júnior, Marketing, Helper
    
    def to_dict(self):
        """Serializa usuário para JSON"""
        return {
            'id': self.id,
            'email': self.email,
            'nome_completo': self.nome_completo,
            'cargo': self.cargo,
            'nome_cargo': self.get_nome_cargo(),
            'empresa_id': self.empresa_id,
            'empresa_nome': self.empresa.nome_fantasia if self.empresa else None,
            'endereco': self.endereco,
            'estado': self.estado,
            'ativo': self.ativo,
            'banido': self.banido,
            'congelado': self.esta_congelado(),
            'criado_em': self.criado_em,
            'ultimo_login': self.ultimo_login,
            'pode_upload': self.pode_fazer_upload(),
            'eh_admin': self.eh_admin(),
            'eh_empresa': self.eh_usuario_empresa()
        }
    
    def __repr__(self):
        return f'<Usuario {self.email} - {self.get_nome_cargo()}>'

# 🔧 Índices para performance
db.Index('idx_usuario_email', Usuario.email)
db.Index('idx_usuario_cargo', Usuario.cargo)
db.Index('idx_usuario_empresa', Usuario.empresa_id)
db.Index('idx_usuario_ativo', Usuario.ativo)