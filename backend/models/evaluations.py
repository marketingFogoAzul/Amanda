from . import db
from config import Config

class Avaliacao(db.Model):
    """
    Modelo de Avaliação - Sistema de avaliações pós-negociação
    """
    
    __tablename__ = 'avaliacoes'
    
    # 🔑 Identificação
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    
    # ⭐ Avaliação
    nota = db.Column(db.Integer, nullable=False)  # 1-5 estrelas
    comentario = db.Column(db.Text)
    
    # 🏷️ Categorias de Avaliação
    atendimento_rapido = db.Column(db.Boolean, default=False)
    proposta_justa = db.Column(db.Boolean, default=False)
    comunicacao_clara = db.Column(db.Boolean, default=False)
    resolucao_eficaz = db.Column(db.Boolean, default=False)
    
    # ⏰ Timestamps
    criado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    atualizado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    
    # 🔗 Relacionamentos
    chat = db.relationship('Chat', back_populates='avaliacoes')
    
    def validar_nota(self):
        """Valida se a nota está entre 1 e 5"""
        return 1 <= self.nota <= 5
    
    def obter_classificacao(self):
        """Retorna classificação textual baseada na nota"""
        if self.nota == 5:
            return "Excelente"
        elif self.nota == 4:
            return "Muito Bom"
        elif self.nota == 3:
            return "Bom"
        elif self.nota == 2:
            return "Regular"
        elif self.nota == 1:
            return "Ruim"
        else:
            return "Não avaliado"
    
    def obter_icone_nota(self):
        """Retorna ícone correspondente à nota"""
        icons = {
            1: "⭐",
            2: "⭐⭐", 
            3: "⭐⭐⭐",
            4: "⭐⭐⭐⭐",
            5: "⭐⭐⭐⭐⭐"
        }
        return icons.get(self.nota, "⭐")
    
    def obter_cor_nota(self):
        """Retorna classe CSS baseada na nota"""
        if self.nota >= 4:
            return "avaliacao-alta"
        elif self.nota == 3:
            return "avaliacao-media"
        else:
            return "avaliacao-baixa"
    
    def possui_comentario(self):
        """Verifica se possui comentário"""
        return bool(self.comentario and self.comentario.strip())
    
    def obter_categorias_selecionadas(self):
        """Retorna lista de categorias selecionadas"""
        categorias = []
        if self.atendimento_rapido:
            categorias.append("Atendimento Rápido")
        if self.proposta_justa:
            categorias.append("Proposta Justa")
        if self.comunicacao_clara:
            categorias.append("Comunicação Clara")
        if self.resolucao_eficaz:
            categorias.append("Resolução Eficaz")
        return categorias
    
    def quantidade_categorias(self):
        """Retorna quantidade de categorias selecionadas"""
        return len(self.obter_categorias_selecionadas())
    
    def tempo_decorrido(self):
        """Calcula tempo desde a avaliação"""
        from datetime import datetime
        
        try:
            criado = datetime.strptime(self.criado_em, '%d/%m/%Y %H:%M:%S')
            agora = datetime.now()
            diferenca = agora - criado
            
            if diferenca.days > 0:
                return f"{diferenca.days} dia(s) atrás"
            elif diferenca.seconds // 3600 > 0:
                return f"{diferenca.seconds // 3600} hora(s) atrás"
            elif diferenca.seconds // 60 > 0:
                return f"{diferenca.seconds // 60} minuto(s) atrás"
            else:
                return "Agora mesmo"
        except:
            return "Tempo indisponível"
    
    def eh_avaliacao_positiva(self):
        """Verifica se é uma avaliação positiva (4-5 estrelas)"""
        return self.nota >= 4
    
    def eh_avaliacao_negativa(self):
        """Verifica se é uma avaliação negativa (1-2 estrelas)"""
        return self.nota <= 2
    
    def eh_avaliacao_neutra(self):
        """Verifica se é uma avaliação neutra (3 estrelas)"""
        return self.nota == 3
    
    def atualizar_avaliacao(self, nota, comentario=None, categorias=None):
        """Atualiza uma avaliação existente"""
        self.nota = nota
        self.comentario = comentario
        self.atualizado_em = Config.get_current_timestamp()
        
        # Resetar categorias
        self.atendimento_rapido = False
        self.proposta_justa = False
        self.comunicacao_clara = False
        self.resolucao_eficaz = False
        
        # Aplicar novas categorias
        if categorias:
            for categoria in categorias:
                if categoria == 'atendimento_rapido':
                    self.atendimento_rapido = True
                elif categoria == 'proposta_justa':
                    self.proposta_justa = True
                elif categoria == 'comunicacao_clara':
                    self.comunicacao_clara = True
                elif categoria == 'resolucao_eficaz':
                    self.resolucao_eficaz = True
    
    def to_dict(self):
        """Serializa avaliação para JSON"""
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'chat_titulo': self.chat.titulo if self.chat else None,
            'usuario_nome': self.chat.usuario.nome_completo if self.chat and self.chat.usuario else None,
            'empresa_nome': self.chat.empresa.nome_fantasia if self.chat and self.chat.empresa else None,
            'nota': self.nota,
            'comentario': self.comentario,
            'classificacao': self.obter_classificacao(),
            'icone_nota': self.obter_icone_nota(),
            'cor_nota': self.obter_cor_nota(),
            'atendimento_rapido': self.atendimento_rapido,
            'proposta_justa': self.proposta_justa,
            'comunicacao_clara': self.comunicacao_clara,
            'resolucao_eficaz': self.resolucao_eficaz,
            'categorias_selecionadas': self.obter_categorias_selecionadas(),
            'quantidade_categorias': self.quantidade_categorias(),
            'criado_em': self.criado_em,
            'atualizado_em': self.atualizado_em,
            'tempo_decorrido': self.tempo_decorrido(),
            'possui_comentario': self.possui_comentario(),
            'eh_positiva': self.eh_avaliacao_positiva(),
            'eh_negativa': self.eh_avaliacao_negativa(),
            'eh_neutra': self.eh_avaliacao_neutra(),
            'valida': self.validar_nota()
        }
    
    def __repr__(self):
        return f'<Avaliacao {self.id} - {self.nota} estrelas - Chat {self.chat_id}>'

# 🔧 Índices para performance
db.Index('idx_avaliacao_chat', Avaliacao.chat_id)
db.Index('idx_avaliacao_nota', Avaliacao.nota)
db.Index('idx_avaliacao_criado_em', Avaliacao.criado_em)
db.Index('idx_avaliacao_atendimento', Avaliacao.atendimento_rapido)
db.Index('idx_avaliacao_proposta', Avaliacao.proposta_justa)
db.Index('idx_avaliacao_comunicacao', Avaliacao.comunicacao_clara)
db.Index('idx_avaliacao_resolucao', Avaliacao.resolucao_eficaz)