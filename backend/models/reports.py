from . import db
from config import Config

class Relatorio(db.Model):
    """
    Modelo de Relatório - Sistema de denúncias e reports
    """
    
    __tablename__ = 'relatorios'
    
    # 🔑 Identificação
    id = db.Column(db.Integer, primary_key=True)
    relator_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    
    # 📝 Conteúdo do Report
    motivo = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), default='outros')  # spam, ofensa, contato, outros
    
    # ⏰ Timestamps
    criado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    
    # 📋 Status do Processamento
    status = db.Column(db.String(50), default='pendente')  # pendente, em_analise, resolvido, descartado
    
    # 👤 Análise do Report
    revisado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    revisado_em = db.Column(db.String(20))
    resolucao = db.Column(db.Text)  # Descrição da resolução
    acao_tomada = db.Column(db.String(100))  # nenhuma, advertência, suspensão, banimento
    
    # 🔗 Relacionamentos
    relator = db.relationship('Usuario', foreign_keys=[relator_id], back_populates='relatorios_feitos')
    chat = db.relationship('Chat', back_populates='relatorios')
    revisor = db.relationship('Usuario', foreign_keys=[revisado_por_id])
    
    def esta_pendente(self):
        """Verifica se o report está pendente"""
        return self.status == 'pendente'
    
    def esta_em_analise(self):
        """Verifica se o report está em análise"""
        return self.status == 'em_analise'
    
    def esta_resolvido(self):
        """Verifica se o report está resolvido"""
        return self.status == 'resolvido'
    
    def foi_descartado(self):
        """Verifica se o report foi descartado"""
        return self.status == 'descartado'
    
    def tempo_decorrido(self):
        """Calcula tempo desde a criação do report"""
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
    
    def marcar_como_analise(self, revisor_id):
        """Marca o report como em análise"""
        self.status = 'em_analise'
        self.revisado_por_id = revisor_id
        self.revisado_em = Config.get_current_timestamp()
    
    def resolver_report(self, resolucao, acao_tomada, revisor_id):
        """Marca o report como resolvido"""
        self.status = 'resolvido'
        self.revisado_por_id = revisor_id
        self.revisado_em = Config.get_current_timestamp()
        self.resolucao = resolucao
        self.acao_tomada = acao_tomada
    
    def descartar_report(self, motivo, revisor_id):
        """Descarta o report"""
        self.status = 'descartado'
        self.revisado_por_id = revisor_id
        self.revisado_em = Config.get_current_timestamp()
        self.resolucao = f"Report descartado: {motivo}"
        self.acao_tomada = 'nenhuma'
    
    def obter_estatisticas_chat(self):
        """Obtém estatísticas do chat relacionado"""
        if self.chat:
            return {
                'total_mensagens': len(self.chat.mensagens),
                'mensagens_usuario': len([msg for msg in self.chat.mensagens if msg.tipo_remetente == 'usuario']),
                'mensagens_amanda': len([msg for msg in self.chat.mensagens if msg.tipo_remetente == 'amanda']),
                'chat_ativo': self.chat.esta_ativo(),
                'chat_assumido': self.chat.esta_assumido()
            }
        return {}
    
    def to_dict(self):
        """Serializa report para JSON"""
        return {
            'id': self.id,
            'relator_id': self.relator_id,
            'relator_nome': self.relator.nome_completo if self.relator else None,
            'chat_id': self.chat_id,
            'chat_titulo': self.chat.titulo if self.chat else None,
            'usuario_chat_nome': self.chat.usuario.nome_completo if self.chat and self.chat.usuario else None,
            'motivo': self.motivo,
            'categoria': self.categoria,
            'criado_em': self.criado_em,
            'status': self.status,
            'revisado_por_id': self.revisado_por_id,
            'revisor_nome': self.revisor.nome_completo if self.revisor else None,
            'revisado_em': self.revisado_em,
            'resolucao': self.resolucao,
            'acao_tomada': self.acao_tomada,
            'tempo_decorrido': self.tempo_decorrido(),
            'esta_pendente': self.esta_pendente(),
            'esta_em_analise': self.esta_em_analise(),
            'esta_resolvido': self.esta_resolvido(),
            'foi_descartado': self.foi_descartado(),
            'estatisticas_chat': self.obter_estatisticas_chat()
        }
    
    def __repr__(self):
        return f'<Relatorio {self.id} - {self.status} - {self.categoria}>'

# 🔧 Índices para performance
db.Index('idx_relatorio_relator', Relatorio.relator_id)
db.Index('idx_relatorio_chat', Relatorio.chat_id)
db.Index('idx_relatorio_status', Relatorio.status)
db.Index('idx_relatorio_categoria', Relatorio.categoria)
db.Index('idx_relatorio_criado_em', Relatorio.criado_em)
db.Index('idx_relatorio_revisado_por', Relatorio.revisado_por_id)