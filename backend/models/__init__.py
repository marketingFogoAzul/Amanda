"""
Models package - Todos os modelos de dados do sistema Amanda AI
"""

from flask_sqlalchemy import SQLAlchemy

# 🔧 Inicializar SQLAlchemy
db = SQLAlchemy()

# 🔄 Importar todos os modelos
from .users import Usuario
# ✅ CORREÇÃO: Importar AvisoEmpresa junto com Empresa
from .companies import Empresa, AvisoEmpresa 
from .chats import Chat, MensagemChat
from .reports import Relatorio
from .evaluations import Avaliacao
from .audit_log import LogAuditoria, LogImportacao

# 📦 Exportar todos os modelos
__all__ = [
    'db',
    'Usuario',
    'Empresa', 
    'AvisoEmpresa', # ✅ Adicionado à lista de exportação
    'Chat',
    'MensagemChat',
    'Relatorio',
    'Avaliacao',
    'LogAuditoria',
    'LogImportacao'
]

print("✅ Models package carregado com sucesso!")