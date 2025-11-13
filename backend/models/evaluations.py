# backend/models/evaluations.py
from app import db
from sqlalchemy.sql import func
import datetime

class Evaluation(db.Model):
    """
    Modelo para o Sistema de Avaliação de Negociações.
    Permite que um usuário avalie como foi a negociação.
    """
    __tablename__ = 'evaluations'
    
    id = db.Column(db.String(36), primary_key=True) # UUID
    
    # A negociação que está sendo avaliada (relação 1 para 1)
    negotiation_id = db.Column(db.String(36), db.ForeignKey('negotiations.id'), unique=True, nullable=False)
    
    # O usuário que fez a avaliação
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Nota (ex: 1 a 5)
    rating = db.Column(db.Integer, nullable=False)
    
    # Comentário (opcional)
    comment = db.Column(db.Text, nullable=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    # Relações
    negotiation = db.relationship('Negotiation', back_populates='evaluation')
    user = db.relationship('User', back_populates='evaluations')

    def __init__(self, id, negotiation_id, user_id, rating, comment=None):
        self.id = id
        self.negotiation_id = negotiation_id
        self.user_id = user_id
        self.rating = rating
        self.comment = comment

    def to_dict(self):
        return {
            'id': self.id,
            'negotiation_id': self.negotiation_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M:%S')
        }

    def __repr__(self):
        return f'<Evaluation {self.id} (Rating: {self.rating})>'