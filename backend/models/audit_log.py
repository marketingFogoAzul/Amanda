from . import db
from config import Config

class LogAuditoria(db.Model):
    """
    Modelo de Log de Auditoria - Registro de todas as ações importantes do sistema
    """
    
    __tablename__ = 'logs_auditoria'
    
    # 🔑 Identificação
    id = db.Column(db.Integer, primary_key=True)
    
    # 👤 Usuário Responsável
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # 📋 Ação Realizada
    acao = db.Column(db.String(100), nullable=False)  # login, registro, chat_criado, etc.
    modulo = db.Column(db.String(50), nullable=False)  # auth, chat, company, import, report
    
    # 🔍 Recurso Afetado
    tipo_recurso = db.Column(db.String(50))  # usuario, empresa, chat, mensagem, etc.
    recurso_id = db.Column(db.Integer)  # ID do recurso afetado
    
    # 📝 Detalhes
    detalhes = db.Column(db.Text)  # JSON com dados adicionais
    status = db.Column(db.String(20), default='sucesso')  # sucesso, erro, aviso
    
    # 🌐 Informações de Rede
    endereco_ip = db.Column(db.String(45))  # Suporte para IPv6
    agente_usuario = db.Column(db.Text)
    
    # ⏰ Timestamp
    criado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    
    # 🔗 Relacionamentos
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    
    def obter_descricao_acao(self):
        """Retorna descrição amigável da ação"""
        descricoes = {
            # 🔐 Autenticação
            'login': 'Login no sistema',
            'logout': 'Logout do sistema',
            'registro': 'Registro de nova conta',
            'ativacao_conta': 'Ativação de conta especial',
            
            # 💬 Chat
            'chat_criado': 'Chat criado',
            'mensagem_enviada': 'Mensagem enviada',
            'chat_assumido': 'Chat assumido por humano',
            'chat_liberado': 'Chat liberado para Amanda',
            'chat_fechado': 'Chat fechado',
            
            # 🏢 Empresa
            'empresa_criada': 'Empresa criada',
            'membro_adicionado': 'Membro adicionado à empresa',
            'membro_removido': 'Membro removido da empresa',
            'aviso_criado': 'Aviso da empresa criado',
            
            # 📊 Reports
            'report_criado': 'Report criado',
            'report_analisado': 'Report analisado',
            'report_resolvido': 'Report resolvido',
            
            # ⭐ Avaliações
            'avaliacao_registrada': 'Avaliação registrada',
            
            # 📤 Importação
            'arquivo_importado': 'Arquivo importado',
            'importacao_processada': 'Importação processada',
            
            # 🔧 Sistema
            'configuracao_alterada': 'Configuração alterada',
            'usuario_banido': 'Usuário banido',
            'usuario_descongelado': 'Usuário descongelado'
        }
        return descricoes.get(self.acao, self.acao)
    
    def obter_icone_acao(self):
        """Retorna ícone correspondente à ação"""
        icones = {
            'login': '🔐',
            'logout': '🚪',
            'registro': '👤',
            'chat_criado': '💬',
            'mensagem_enviada': '📨',
            'empresa_criada': '🏢',
            'report_criado': '🚨',
            'avaliacao_registrada': '⭐',
            'arquivo_importado': '📤',
            'usuario_banido': '🔨'
        }
        return icones.get(self.acao, '📝')
    
    def obter_cor_status(self):
        """Retorna cor baseada no status"""
        cores = {
            'sucesso': 'verde',
            'erro': 'vermelho',
            'aviso': 'amarelo'
        }
        return cores.get(self.status, 'cinza')
    
    def foi_sucesso(self):
        """Verifica se a ação foi bem sucedida"""
        return self.status == 'sucesso'
    
    def foi_erro(self):
        """Verifica se a ação resultou em erro"""
        return self.status == 'erro'
    
    def possui_detalhes(self):
        """Verifica se possui detalhes adicionais"""
        return bool(self.detalhes and self.detalhes.strip())
    
    def parse_detalhes(self):
        """Tenta fazer parse dos detalhes como JSON"""
        import json
        try:
            if self.detalhes:
                return json.loads(self.detalhes)
        except:
            pass
        return {}
    
    def tempo_decorrido(self):
        """Calcula tempo desde o log"""
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
    
    def to_dict(self):
        """Serializa log para JSON"""
        detalhes_parsed = self.parse_detalhes()
        
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome_completo if self.usuario else 'Sistema',
            'acao': self.acao,
            'descricao_acao': self.obter_descricao_acao(),
            'icone_acao': self.obter_icone_acao(),
            'modulo': self.modulo,
            'tipo_recurso': self.tipo_recurso,
            'recurso_id': self.recurso_id,
            'detalhes': detalhes_parsed,
            'detalhes_raw': self.detalhes,
            'status': self.status,
            'cor_status': self.obter_cor_status(),
            'endereco_ip': self.endereco_ip,
            'agente_usuario': self.agente_usuario,
            'criado_em': self.criado_em,
            'tempo_decorrido': self.tempo_decorrido(),
            'foi_sucesso': self.foi_sucesso(),
            'foi_erro': self.foi_erro(),
            'possui_detalhes': self.possui_detalhes()
        }
    
    def __repr__(self):
        return f'<LogAuditoria {self.id} - {self.acao} - {self.status}>'

class LogImportacao(db.Model):
    """
    Modelo de Log de Importação - Registro de importações de planilhas
    """
    
    __tablename__ = 'logs_importacao'
    
    # 🔑 Identificação
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # 📁 Arquivo
    nome_arquivo = db.Column(db.String(255), nullable=False)
    tipo_arquivo = db.Column(db.String(10), nullable=False)  # csv, xlsx, xls
    tamanho_arquivo = db.Column(db.Integer)  # Em bytes
    
    # 📊 Resultados
    quantidade_linhas = db.Column(db.Integer)
    sucesso_quantidade = db.Column(db.Integer)
    erro_quantidade = db.Column(db.Integer)
    erros = db.Column(db.Text)  # JSON com detalhes dos erros
    
    # 📈 Status
    status = db.Column(db.String(20), default='processando')  # processando, concluido, falhou
    
    # ⏰ Timestamps
    criado_em = db.Column(db.String(20), default=Config.get_current_timestamp)
    concluido_em = db.Column(db.String(20))
    
    # 🔗 Relacionamentos
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], back_populates='logs_importacao')
    
    def obter_taxa_sucesso(self):
        """Calcula taxa de sucesso"""
        if self.quantidade_linhas and self.quantidade_linhas > 0:
            return (self.sucesso_quantidade / self.quantidade_linhas) * 100
        return 0
    
    def esta_processando(self):
        """Verifica se ainda está processando"""
        return self.status == 'processando'
    
    def foi_concluido(self):
        """Verifica se foi concluído com sucesso"""
        return self.status == 'concluido'
    
    def falhou(self):
        """Verifica se falhou"""
        return self.status == 'falhou'
    
    def obter_tamanho_formatado(self):
        """Retorna tamanho do arquivo formatado"""
        if not self.tamanho_arquivo:
            return "N/A"
        
        if self.tamanho_arquivo < 1024:
            return f"{self.tamanho_arquivo} B"
        elif self.tamanho_arquivo < 1024 * 1024:
            return f"{self.tamanho_arquivo / 1024:.1f} KB"
        else:
            return f"{self.tamanho_arquivo / (1024 * 1024):.1f} MB"
    
    def parse_erros(self):
        """Tenta fazer parse dos erros como JSON"""
        import json
        try:
            if self.erros:
                return json.loads(self.erros)
        except:
            pass
        return []
    
    def tempo_processamento(self):
        """Calcula tempo total de processamento"""
        from datetime import datetime
        
        try:
            if self.criado_em and self.concluido_em:
                inicio = datetime.strptime(self.criado_em, '%d/%m/%Y %H:%M:%S')
                fim = datetime.strptime(self.concluido_em, '%d/%m/%Y %H:%M:%S')
                diferenca = fim - inicio
                return f"{diferenca.total_seconds():.1f} segundos"
        except:
            pass
        return "N/A"
    
    def to_dict(self):
        """Serializa log de importação para JSON"""
        erros_parsed = self.parse_erros()
        
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome_completo if self.usuario else None,
            'nome_arquivo': self.nome_arquivo,
            'tipo_arquivo': self.tipo_arquivo,
            'tamanho_arquivo': self.tamanho_arquivo,
            'tamanho_formatado': self.obter_tamanho_formatado(),
            'quantidade_linhas': self.quantidade_linhas,
            'sucesso_quantidade': self.sucesso_quantidade,
            'erro_quantidade': self.erro_quantidade,
            'taxa_sucesso': self.obter_taxa_sucesso(),
            'erros': erros_parsed,
            'erros_raw': self.erros,
            'status': self.status,
            'criado_em': self.criado_em,
            'concluido_em': self.concluido_em,
            'tempo_processamento': self.tempo_processamento(),
            'esta_processando': self.esta_processando(),
            'foi_concluido': self.foi_concluido(),
            'falhou': self.falhou()
        }
    
    def __repr__(self):
        return f'<LogImportacao {self.id} - {self.nome_arquivo} - {self.status}>'

# 🔧 Índices para performance
db.Index('idx_log_auditoria_usuario', LogAuditoria.usuario_id)
db.Index('idx_log_auditoria_acao', LogAuditoria.acao)
db.Index('idx_log_auditoria_modulo', LogAuditoria.modulo)
db.Index('idx_log_auditoria_status', LogAuditoria.status)
db.Index('idx_log_auditoria_criado_em', LogAuditoria.criado_em)

db.Index('idx_log_importacao_usuario', LogImportacao.usuario_id)
db.Index('idx_log_importacao_status', LogImportacao.status)
db.Index('idx_log_importacao_criado_em', LogImportacao.criado_em)