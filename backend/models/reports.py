# backend/models/reports.py
from app import db
from sqlalchemy.sql import func
import datetime

class Report(db.Model):
    """
    Modelo para o Sistema de Denúncias (Reports).
    """
    __tablename__ = 'reports'
    
    id = db.Column(db.String(36), primary_key=True) # UUID
    
    # Quem denunciou
    reporter_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Quem foi denunciado
    reported_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # (Opcional) A negociação onde ocorreu o problema
    negotiation_id = db.Column(db.String(36), db.ForeignKey('negotiations.id'), nullable=True)
    
    # (Opcional) A mensagem específica
    message_id = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=True)
    
    # Categoria da denúncia: 'spam', 'abuso', 'contato_externo', 'fraude', 'outro'
    category = db.Column(db.String(100), nullable=False)
    
    # Descrição
    description = db.Column(db.Text, nullable=False)
    
    # Status: 'pending', 'resolved', 'dismissed'
    status = db.Column(db.String(50), default='pending', nullable=False)
    
    # Quem resolveu (Admin/Helper)
    resolved_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relações
    reporter = db.relationship('User', foreign_keys=[reporter_id], back_populates='reports_made')
    reported_user = db.relationship('User', foreign_keys=[reported_user_id], back_populates='reports_received')
    resolver = db.relationship('User', foreign_keys=[resolved_by_id])
    
    negotiation = db.relationship('Negotiation')
    message = db.relationship('Message')

    def __repr__(self):
        return f'<Report {self.id} (Category: {self.category}, Status: {self.status})>'