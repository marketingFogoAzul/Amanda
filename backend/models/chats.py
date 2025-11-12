from . import db
from config import Config

class Chat(db.Model):
    """
    Modelo de Chat - Conversas entre usuários e Amanda AI
    """
    
    __tablename__ = 'chats'
    
    # 🔑 Identificação
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'))
    
    # 📝 Informações do Chat
    titulo = db.Column(db.String(255))
    status = db.Column(db.String(50), default='ativo')  # ativo, assumido, fechado, reportado
    
    # 👥 Atendimento Humano
    assumido_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    assumido_em = db.Column(db.String(20))
    
    # ⏰ Timestamps
    criado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    fechado_em = db.Column(db.String(20))
    atualizado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    
    # 🔗 Relacionamentos
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], back_populates='chats')
    empresa = db.relationship('Empresa', back_populates='chats')
    assumido_por = db.relationship('Usuario', foreign_keys=[assumido_por_id], back_populates='chats_assumidos')
    mensagens = db.relationship('MensagemChat', back_populates='chat', cascade='all, delete-orphan')
    avaliacoes = db.relationship('Avaliacao', back_populates='chat', cascade='all, delete-orphan')
    relatorios = db.relationship('Relatorio', back_populates='chat', cascade='all, delete-orphan')
    
    def quantidade_mensagens(self):
        """Retorna quantidade total de mensagens"""
        return len(self.mensagens)
    
    def quantidade_mensagens_usuario(self):
        """Retorna quantidade de mensagens do usuário"""
        return len([msg for msg in self.mensagens if msg.tipo_remetente == 'usuario'])
    
    def quantidade_mensagens_amanda(self):
        """Retorna quantidade de mensagens da Amanda"""
        return len([msg for msg in self.mensagens if msg.tipo_remetente == 'amanda'])
    
    def ultima_mensagem(self):
        """Retorna a última mensagem do chat"""
        if self.mensagens:
            return sorted(self.mensagens, key=lambda x: x.timestamp, reverse=True)[0]
        return None
    
    def esta_ativo(self):
        """Verifica se o chat está ativo"""
        return self.status == 'ativo'
    
    def esta_assumido(self):
        """Verifica se o chat está sendo atendido por humano"""
        return self.status == 'assumido' and self.assumido_por_id is not None
    
    def esta_fechado(self):
        """Verifica se o chat está fechado"""
        return self.status == 'fechado'
    
    def foi_avaliado(self):
        """Verifica se o chat foi avaliado"""
        return len(self.avaliacoes) > 0
    
    def tempo_decorrido(self):
        """Calcula tempo desde a criação do chat"""
        from datetime import datetime
        
        try:
            criado = datetime.strptime(self.criado_em, '%d/%m/%Y %H:%M:%S')
            agora = datetime.now()
            diferenca = agora - criado
            
            if diferenca.days > 0:
                return f"{diferenca.days} dia(s)"
            elif diferenca.seconds // 3600 > 0:
                return f"{diferenca.seconds // 3600} hora(s)"
            else:
                return f"{diferenca.seconds // 60} minuto(s)"
        except:
            return "Tempo indisponível"
    
    def assumir_chat(self, usuario_id):
        """Método para assumir o chat por um representante"""
        self.assumido_por_id = usuario_id
        self.assumido_em = Config.get_current_timestamp()
        self.status = 'assumido'
        
        # Criar mensagem do sistema
        mensagem_sistema = MensagemChat(
            chat_id=self.id,
            tipo_remetente='sistema',
            conteudo=f'Chat assumido por {self.assumido_por.nome_completo}. Amanda AI não responderá mais neste chat.'
        )
        db.session.add(mensagem_sistema)
    
    def liberar_chat(self):
        """Método para liberar o chat de volta para Amanda AI"""
        self.assumido_por_id = None
        self.assumido_em = None
        self.status = 'ativo'
        
        # Criar mensagem do sistema
        mensagem_sistema = MensagemChat(
            chat_id=self.id,
            tipo_remetente='sistema',
            conteudo='Chat liberado. Amanda AI retomará o atendimento.'
        )
        db.session.add(mensagem_sistema)
    
    def fechar_chat(self):
        """Método para fechar o chat"""
        self.status = 'fechado'
        self.fechado_em = Config.get_current_timestamp()
    
    def to_dict(self):
        """Serializa chat para JSON"""
        ultima_msg = self.ultima_mensagem()
        
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome_completo if self.usuario else None,
            'empresa_id': self.empresa_id,
            'empresa_nome': self.empresa.nome_fantasia if self.empresa else None,
            'titulo': self.titulo,
            'status': self.status,
            'assumido_por_id': self.assumido_por_id,
            'assumido_por_nome': self.assumido_por.nome_completo if self.assumido_por else None,
            'assumido_em': self.assumido_em,
            'criado_em': self.criado_em,
            'fechado_em': self.fechado_em,
            'quantidade_mensagens': self.quantidade_mensagens(),
            'quantidade_mensagens_usuario': self.quantidade_mensagens_usuario(),
            'quantidade_mensagens_amanda': self.quantidade_mensagens_amanda(),
            'ultima_mensagem': ultima_msg.conteudo if ultima_msg else None,
            'ultima_mensagem_tipo': ultima_msg.tipo_remetente if ultima_msg else None,
            'ultima_mensagem_timestamp': ultima_msg.timestamp if ultima_msg else None,
            'tempo_decorrido': self.tempo_decorrido(),
            'esta_ativo': self.esta_ativo(),
            'esta_assumido': self.esta_assumido(),
            'esta_fechado': self.esta_fechado(),
            'foi_avaliado': self.foi_avaliado()
        }
    
    def __repr__(self):
        return f'<Chat {self.id} - {self.usuario.nome_completo if self.usuario else "Sem usuário"}>'

class MensagemChat(db.Model):
    """
    Modelo de Mensagem - Mensagens individuais do chat
    """
    
    __tablename__ = 'mensagens_chat'
    
    # 🔑 Identificação
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    
    # 💬 Conteúdo da Mensagem
    tipo_remetente = db.Column(db.String(20), nullable=False)  # usuario, amanda, humano, sistema
    conteudo = db.Column(db.Text, nullable=False)
    
    # ⏰ Timestamp
    timestamp = db.Column(db.String(20), default=Config.get_current_timestamp)
    
    # 🚫 Moderação
    removida = db.Column(db.Boolean, default=False)
    motivo_remocao = db.Column(db.Text)
    removida_em = db.Column(db.String(20))
    removida_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # 🔗 Relacionamentos
    chat = db.relationship('Chat', back_populates='mensagens')
    removida_por = db.relationship('Usuario', foreign_keys=[removida_por_id])
    
    def eh_usuario(self):
        """Verifica se a mensagem é do usuário"""
        return self.tipo_remetente == 'usuario'
    
    def eh_amanda(self):
        """Verifica se a mensagem é da Amanda AI"""
        return self.tipo_remetente == 'amanda'
    
    def eh_humano(self):
        """Verifica se a mensagem é de um atendente humano"""
        return self.tipo_remetente == 'humano'
    
    def eh_sistema(self):
        """Verifica se a mensagem é do sistema"""
        return self.tipo_remetente == 'sistema'
    
    def remover_mensagem(self, motivo, usuario_id=None):
        """Método para remover uma mensagem"""
        self.removida = True
        self.motivo_remocao = motivo
        self.removida_em = Config.get_current_timestamp()
        self.removida_por_id = usuario_id
        
        # Substitui conteúdo por mensagem padrão
        self.conteudo = '[MENSAGEM REMOVIDA PELA MODERAÇÃO]'
    
    def conteudo_para_exibicao(self):
        """Retorna conteúdo seguro para exibição"""
        if self.removida:
            return f'[MENSAGEM REMOVIDA] Motivo: {self.motivo_remocao}'
        return self.conteudo
    
    def to_dict(self):
        """Serializa mensagem para JSON"""
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'tipo_remetente': self.tipo_remetente,
            'conteudo': self.conteudo_para_exibicao(),
            'conteudo_original': self.conteudo if not self.removida else None,
            'timestamp': self.timestamp,
            'removida': self.removida,
            'motivo_remocao': self.motivo_remocao,
            'removida_em': self.removida_em,
            'removida_por_id': self.removida_por_id,
            'eh_usuario': self.eh_usuario(),
            'eh_amanda': self.eh_amanda(),
            'eh_humano': self.eh_humano(),
            'eh_sistema': self.eh_sistema()
        }
    
    def __repr__(self):
        return f'<Mensagem {self.id} - {self.tipo_remetente}>'

# 🔧 Índices para performance
db.Index('idx_chat_usuario', Chat.usuario_id)
db.Index('idx_chat_empresa', Chat.empresa_id)
db.Index('idx_chat_status', Chat.status)
db.Index('idx_chat_assumido_por', Chat.assumido_por_id)
db.Index('idx_chat_criado_em', Chat.criado_em)

db.Index('idx_mensagem_chat', MensagemChat.chat_id)
db.Index('idx_mensagem_timestamp', MensagemChat.timestamp)
db.Index('idx_mensagem_tipo', MensagemChat.tipo_remetente)
db.Index('idx_mensagem_removida', MensagemChat.removida)