# backend/models/chats.py
from app import db
from sqlalchemy.sql import func
import datetime

class Chat(db.Model):
    """
    Modelo para uma sessão de Chat.
    Agrupa uma sequência de mensagens entre um usuário e a IA.
    """
    __tablename__ = 'chats'
    
    id = db.Column(db.String(36), primary_key=True) # UUID
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Contexto do chat (ex: "Negociação Pedido #123")
    title = db.Column(db.String(255), nullable=True) 
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    
    # Relações
    user = db.relationship('User', back_populates='chats')
    messages = db.relationship('Message', back_populates='chat', cascade="all, delete-orphan")
    negotiation = db.relationship('Negotiation', back_populates='chat', uselist=False) # Um chat por negociação

    def __repr__(self):
        return f'<Chat {self.id} (User: {self.user_id})>'

class Message(db.Model):
    """
    Modelo para uma Mensagem individual dentro de um Chat.
    """
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True) # UUID
    chat_id = db.Column(db.String(36), db.ForeignKey('chats.id'), nullable=False, index=True)
    
    # Define quem enviou: 'user' ou 'amanda' (IA)
    sender_role = db.Column(db.String(20), nullable=False) 
    
    # Conteúdo da mensagem
    content = db.Column(db.Text, nullable=False)
    
    # Flag para moderação (se a mensagem foi bloqueada)
    is_moderated = db.Column(db.Boolean, default=False)
    moderation_reason = db.Column(db.String(255), nullable=True)
    
    # Timestamp (Formato DD/MM/YYYY HH:MM:SS)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Relação
    chat = db.relationship('Chat', back_populates='messages')

    def to_dict(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'sender_role': self.sender_role,
            'content': self.content,
            'is_moderated': self.is_moderated,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M:%S') # Formato específico
        }

    def __repr__(self):
        return f'<Message {self.id} (Sender: {self.sender_role})>'