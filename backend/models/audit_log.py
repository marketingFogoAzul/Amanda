# backend/models/audit_log.py
from app import db
from sqlalchemy.sql import func
import datetime

class AuditLog(db.Model):
    """
    Modelo para Logs de Auditoria.
    Registra ações críticas no sistema.
    """
    __tablename__ = 'audit_logs'
    
    # Usamos BigInteger para um ID que crescerá rapidamente
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # Usuário que realizou a ação (pode ser nulo se for 'system')
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)
    
    # IP de origem da ação
    ip_address = db.Column(db.String(45), nullable=True) 
    
    # Ação realizada (ex: 'login_success', 'user_blocked', 'report_created')
    action = db.Column(db.String(100), nullable=False, index=True)
    
    # (Opcional) Tipo do objeto alvo (ex: 'user', 'negotiation', 'company')
    target_type = db.Column(db.String(50), nullable=True)
    
    # (Opcional) ID do objeto alvo
    target_id = db.Column(db.String(36), nullable=True, index=True)
    
    # Detalhes extras em formato JSON
    # Ex: {"motivo_bloqueio": "Troca de contato", "dias": 3}
    details_json = db.Column(db.Text, nullable=True)
    
    # Timestamp
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    # Relação
    user = db.relationship('User', back_populates='audit_logs')

    def __init__(self, action, user_id=None, ip_address=None, target_type=None, target_id=None, details_json=None):
        self.action = action
        self.user_id = user_id
        self.ip_address = ip_address
        self.target_type = target_type
        self.target_id = target_id
        self.details_json = details_json

    def __repr__(self):
        return f'<AuditLog {self.id} (Action: {self.action}, User: {self.user_id})>'