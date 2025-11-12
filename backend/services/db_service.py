import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from werkzeug.security import generate_password_hash

# Importa os modelos e a instância do SQLAlchemy
from models import db, Usuario, Empresa, Chat, LogAuditoria, Relatorio, LogImportacao
from config import Config

class DBService:
    """
    Serviço de Banco de Dados de Alto Nível.
    Centraliza operações de persistência e consultas complexas, especialmente
    para funções administrativas e de moderação de usuários.
    """

    def _log_action(self, usuario_id: Optional[int], acao: str, modulo: str, tipo_recurso: str, detalhes: str, status: str = 'sucesso', recurso_id: Optional[int] = None):
        """Função auxiliar para criar um Log de Auditoria."""
        log = LogAuditoria(
            usuario_id=usuario_id,
            acao=acao,
            modulo=modulo,
            tipo_recurso=tipo_recurso,
            detalhes=detalhes,
            status=status,
            recurso_id=recurso_id,
            endereco_ip="N/A",  # Em um ambiente real, pegaríamos o IP do request
            agente_usuario="N/A" # Em um ambiente real, pegaríamos o User-Agent do request
        )
        db.session.add(log)

    # --- Funções de Moderação de Usuário (Painel ZIPBUM) ---

    def ban_user(self, admin_id: int, user_id: int, motivo: str) -> bool:
        """Bane um usuário permanentemente."""
        usuario = Usuario.query.get(user_id)
        if not usuario:
            self._log_action(admin_id, 'usuario_banimento_falha', 'admin', 'usuario', f'Tentativa de banir usuário {user_id} falhou: não encontrado', 'erro')
            return False

        usuario.banido = True
        usuario.motivo_banimento = motivo
        usuario.ativo = False
        usuario.congelado_ate = None
        usuario.atualizado_em = Config.get_current_timestamp()

        self._log_action(admin_id, 'usuario_banido', 'admin', 'usuario', f'Usuário {usuario.email} banido. Motivo: {motivo}', recurso_id=user_id)
        db.session.commit()
        return True

    def unban_user(self, admin_id: int, user_id: int) -> bool:
        """Remove o banimento de um usuário."""
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return False

        usuario.banido = False
        usuario.motivo_banimento = None
        usuario.ativo = True
        usuario.atualizado_em = Config.get_current_timestamp()

        self._log_action(admin_id, 'usuario_desbanido', 'admin', 'usuario', f'Usuário {usuario.email} desbanido.', recurso_id=user_id)
        db.session.commit()
        return True

    def freeze_user(self, admin_id: int, user_id: int, days: int, motivo: str) -> bool:
        """Congela (suspende) um usuário por X dias."""
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return False

        freeze_date = datetime.now() + timedelta(days=days)
        usuario.congelado_ate = freeze_date.strftime('%d/%m/%Y %H:%M:%S')
        usuario.atualizado_em = Config.get_current_timestamp()

        self._log_action(admin_id, 'usuario_congelado', 'admin', 'usuario', f'Usuário {usuario.email} congelado até {usuario.congelado_ate}. Motivo: {motivo}', status='aviso', recurso_id=user_id)
        db.session.commit()
        return True

    def reset_password(self, admin_id: int, user_id: int) -> Optional[str]:
        """Gera uma nova senha temporária para o usuário."""
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return None

        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        usuario.senha_hash = generate_password_hash(temp_password)
        usuario.atualizado_em = Config.get_current_timestamp()

        self._log_action(admin_id, 'senha_resetada', 'admin', 'usuario', f'Senha do usuário {usuario.email} resetada por administrador.', status='aviso', recurso_id=user_id)
        db.session.commit()

        # Em um ambiente real, esta senha seria enviada por e-mail, não retornada.
        return temp_password

    # --- Funções de Estatísticas e Relatórios de Sistema (Painel ZIPBUM) ---

    def get_global_metrics(self) -> Dict[str, Any]:
        """Obtém métricas globais para o Painel ZIPBUM (Admin)."""
        
        # Métrica: Total de Usuários
        total_users = Usuario.query.count()
        
        # Métrica: Total de Empresas
        total_companies = Empresa.query.count()
        
        # Métrica: Chats
        chats_stats = db.session.query(
            db.func.count(Chat.id),
            Chat.status
        ).group_by(Chat.status).all()
        
        chats_dict = {status: count for count, status in chats_stats}
        total_chats = sum(chats_dict.values())
        
        # Métrica: Reports Pendentes
        pending_reports = Relatorio.query.filter_by(status='pendente').count()
        
        # Métrica: Total de Log de Importação
        total_imports = LogImportacao.query.count()

        return {
            'total_users': total_users,
            'total_companies': total_companies,
            'total_chats': total_chats,
            'chats_by_status': chats_dict,
            'pending_reports': pending_reports,
            'total_imports': total_imports,
            'system_time': Config.get_current_timestamp()
        }

    def get_users_list_for_admin(self, page: int, per_page: int, search_term: str) -> Dict[str, Any]:
        """Obtém lista de usuários com paginação e status para o painel admin."""
        
        query = Usuario.query.order_by(Usuario.criado_em.desc())
        
        if search_term:
            query = query.filter(
                (Usuario.nome_completo.ilike(f'%{search_term}%')) |
                (Usuario.email.ilike(f'%{search_term}%'))
            )
            
        paginated_users = query.paginate(page=page, per_page=per_page, error_out=False)
        
        user_list = []
        for user in paginated_users.items:
            user_data = user.to_dict()
            
            # Adicionar status específico para UI Admin
            if user.banido:
                user_data['admin_status'] = 'Banido'
            elif user.esta_congelado():
                user_data['admin_status'] = f"Congelado até {user.congelado_ate.split(' ')[0]}"
            elif not user.ativo:
                 user_data['admin_status'] = 'Inativo' # Para usuários que não tem o flag 'ativo'=True
            else:
                user_data['admin_status'] = 'Disponível'
                
            user_list.append(user_data)
            
        return {
            'users': user_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated_users.total,
                'pages': paginated_users.pages
            }
        }