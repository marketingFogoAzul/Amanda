from . import db
from config import Config

class Empresa(db.Model):
    """
    Modelo de Empresa - Cadastro completo de empresas
    """
    
    __tablename__ = 'empresas'
    
    # 🔑 Identificação
    id = db.Column(db.Integer, primary_key=True)
    cnpj = db.Column(db.String(18), unique=True, nullable=False, index=True)
    razao_social = db.Column(db.String(255), nullable=False)
    nome_fantasia = db.Column(db.String(255), nullable=False)
    
    # 📍 Contato e Localização
    endereco = db.Column(db.String(300))
    estado = db.Column(db.String(2))  # UF
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # ⏰ Timestamps
    criado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    atualizado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    
    # 🔒 Status
    ativa = db.Column(db.Boolean, default=True)
    
    # 🔗 Relacionamentos
    usuarios = db.relationship('Usuario', back_populates='empresa')
    chats = db.relationship('Chat', back_populates='empresa')
    avisos = db.relationship('AvisoEmpresa', back_populates='empresa')
    
    def quantidade_usuarios_ativos(self):
        """Retorna quantidade de usuários ativos na empresa"""
        return len([u for u in self.usuarios if u.ativo])
    
    def representante_principal(self):
        """Retorna o representante principal da empresa"""
        for usuario in self.usuarios:
            if usuario.cargo == 4:  # Representante
                return usuario
        return None
    
    def to_dict(self):
        """Serializa empresa para JSON"""
        return {
            'id': self.id,
            'cnpj': self.cnpj,
            'razao_social': self.razao_social,
            'nome_fantasia': self.nome_fantasia,
            'endereco': self.endereco,
            'estado': self.estado,
            'telefone': self.telefone,
            'email': self.email,
            'criado_em': self.criado_em,
            'ativa': self.ativa,
            'quantidade_usuarios': len(self.usuarios),
            'quantidade_usuarios_ativos': self.quantidade_usuarios_ativos(),
            'representante_principal': self.representante_principal().nome_completo if self.representante_principal() else None
        }
    
    def __repr__(self):
        return f'<Empresa {self.nome_fantasia} - {self.cnpj}>'

class AvisoEmpresa(db.Model):
    """
    Modelo de Avisos da Empresa - Comunicação interna
    """
    
    __tablename__ = 'avisos_empresa'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    titulo = db.Column(db.String(255), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    criado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    atualizado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    ativo = db.Column(db.Boolean, default=True)
    
    # 🔗 Relacionamentos
    empresa = db.relationship('Empresa', back_populates='avisos')
    autor = db.relationship('Usuario', foreign_keys=[criado_por_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'titulo': self.titulo,
            'conteudo': self.conteudo,
            'criado_por_id': self.criado_por_id,
            'autor_nome': self.autor.nome_completo if self.autor else None,
            'criado_em': self.criado_em,
            'atualizado_em': self.atualizado_em,
            'ativo': self.ativo
        }

# 🔧 Índices
db.Index('idx_empresa_cnpj', Empresa.cnpj)
db.Index('idx_empresa_ativa', Empresa.ativa)
db.Index('idx_aviso_empresa', AvisoEmpresa.empresa_id)
db.Index('idx_aviso_ativo', AvisoEmpresa.ativo)