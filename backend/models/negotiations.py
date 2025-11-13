# backend/models/negotiations.py
from app import db
from sqlalchemy.sql import func
import datetime

class Negotiation(db.Model):
    """
    Modelo para a Negociação B2B principal.
    Vincula as empresas, o chat e o status.
    """
    __tablename__ = 'negotiations'
    
    id = db.Column(db.String(36), primary_key=True) # UUID
    
    # Vincula ao chat onde esta negociação ocorre
    chat_id = db.Column(db.String(36), db.ForeignKey('chats.id'), unique=True, nullable=False)
    
    # Quem está vendendo
    seller_company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=False, index=True)
    # Quem está comprando
    buyer_company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Status: 'active', 'closed_success', 'closed_fail', 'reported'
    status = db.Column(db.String(50), default='active', nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    
    # Relações
    chat = db.relationship('Chat', back_populates='negotiation')
    seller_company = db.relationship('Company', foreign_keys=[seller_company_id], back_populates='negotiations_as_seller')
    buyer_company = db.relationship('Company', foreign_keys=[buyer_company_id], back_populates='negotiations_as_buyer')
    
    proposals = db.relationship('Proposal', back_populates='negotiation', cascade="all, delete-orphan")
    evaluation = db.relationship('Evaluation', back_populates='negotiation', uselist=False)

    def __repr__(self):
        return f'<Negotiation {self.id} (Status: {self.status})>'

class Proposal(db.Model):
    """
    Modelo para uma Proposta (oferta ou contra-oferta)
    feita dentro de uma Negociação.
    """
    __tablename__ = 'proposals'
    
    id = db.Column(db.String(36), primary_key=True) # UUID
    negotiation_id = db.Column(db.String(36), db.ForeignKey('negotiations.id'), nullable=False, index=True)
    
    # Quem fez a proposta (ID do Usuário)
    proposer_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Detalhes da proposta (pode ser um JSON complexo)
    # Ex: {"items": [{"sku": "123", "qty": 100, "price": 10.50}], "payment": "30 dias"}
    details_json = db.Column(db.Text, nullable=False)
    
    # Valor total da proposta para referência rápida
    total_value = db.Column(db.Float, nullable=True)
    
    # Status: 'sent', 'viewed', 'accepted', 'rejected', 'retracted'
    status = db.Column(db.String(50), default='sent', nullable=False)
    
    # Timestamp (Formato DD/MM/YYYY HH:MM:SS)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    # Relações
    negotiation = db.relationship('Negotiation', back_populates='proposals')
    proposer = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'negotiation_id': self.negotiation_id,
            'proposer_user_id': self.proposer_user_id,
            'details': json.loads(self.details_json) if self.details_json else {},
            'total_value': self.total_value,
            'status': self.status,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M:%S')
        }

    def __repr__(self):
        return f'<Proposal {self.id} (Status: {self.status})>'