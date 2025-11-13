# backend/models/companies.py
import datetime
from app import db
from sqlalchemy.sql import func

class Company(db.Model):
    """
    Modelo para Empresas (Clientes ZIPBUM).
    """
    __tablename__ = 'companies'
    
    # Usamos String(36) para armazenar um UUID (como string)
    id = db.Column(db.String(36), primary_key=True) 
    # Formato: 00.000.000/0000-00 (18 chars)
    cnpj = db.Column(db.String(18), unique=True, nullable=False, index=True) 
    razao_social = db.Column(db.String(255), nullable=False)
    nome_fantasia = db.Column(db.String(255), nullable=True)
    
    # Endereço
    uf = db.Column(db.String(2), nullable=False) # Estado (UF)
    cidade = db.Column(db.String(100), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    
    # Relação inversa: uma empresa pode ter muitos usuários
    users = db.relationship('User', back_populates='company')
    
    # Relação com negociações (a empresa como vendedora ou compradora)
    # (Serão ativadas quando criarmos o modelo Negotiation)
    # negotiations_as_seller = db.relationship('Negotiation', 
    #                                          foreign_keys='Negotiation.seller_company_id', 
    #                                          back_populates='seller_company')
    # negotiations_as_buyer = db.relationship('Negotiation', 
    #                                         foreign_keys='Negotiation.buyer_company_id', 
    #                                         back_populates='buyer_company')

    def __init__(self, id, cnpj, razao_social, uf, nome_fantasia=None, cidade=None):
        self.id = id
        self.cnpj = cnpj
        self.razao_social = razao_social
        self.uf = uf
        self.nome_fantasia = nome_fantasia
        self.cidade = cidade

    def to_dict(self):
        """Retorna um dicionário serializável da empresa."""
        return {
            'id': self.id,
            'cnpj': self.cnpj,
            'razao_social': self.razao_social,
            'nome_fantasia': self.nome_fantasia,
            'uf': self.uf,
            'cidade': self.cidade,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Company {self.razao_social} (CNPJ: {self.cnpj})>'