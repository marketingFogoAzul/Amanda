# backend/routes/chat.py

from flask import request, jsonify
from . import chat_bp # Importa o Blueprint
from models.users import User
from models.chats import Chat, Message
from models.negotiations import Negotiation
from services.ai_service import AIService
from services.moderation_service import ModerationService
from services.date_service import DateService
from utils.security import jwt_required, get_user_identity
from utils.constants import SenderRoles, Cargos
from services.role_service import roles_required
from app import db
import uuid
import json

@chat_bp.route('/new', methods=['POST'])
@jwt_required()
def create_new_chat():
    """
    Cria uma nova sessão de chat.
    Opcionalmente, pode receber um 'negotiation_id' para vincular.
    """
    user_id = get_user_identity()
    data = request.json
    title = data.get('title', 'Nova Negociação')
    
    try:
        new_chat = Chat(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title
        )
        db.session.add(new_chat)
        db.session.commit()
        
        return jsonify({
            "message": "Chat criado com sucesso.",
            "chat_id": new_chat.id,
            "title": new_chat.title,
            "created_at": DateService.format_date(new_chat.created_at)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar novo chat: {e}")
        return jsonify({"error": "Erro interno ao iniciar chat."}), 500

@chat_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    """
    Recebe uma mensagem do usuário, processa (moderação + IA) e retorna a resposta.
    """
    user_id = get_user_identity()
    data = request.json
    
    chat_id = data.get('chat_id')
    user_content = data.get('content')

    if not chat_id or not user_content:
        return jsonify({"error": "chat_id e content são obrigatórios."}), 400

    # 1. Verifica se o Chat existe e o usuário tem permissão
    chat = Chat.query.get(chat_id)
    user = User.query.get(user_id)
    
    if not chat:
        return jsonify({"error": "Chat não encontrado."}), 404
    if chat.user_id != user_id and user.role.permission_level > Cargos.HELPER_N3:
         # Apenas o próprio usuário ou um admin/helper podem ver o chat
        return jsonify({"error": "Acesso negado a este chat."}), 403

    # 2. Moderação (Etapa Crítica)
    is_blocked, reason = ModerationService.check_message(user_content)
    
    if is_blocked:
        # 2a. Se for bloqueado:
        # Aplica a penalidade
        ModerationService.apply_block(user, reason)
        # Gera a mensagem de bloqueio
        block_message_content = ModerationService.get_block_message(reason)
        
        # Salva a mensagem do *usuário* como "moderada" (para registro)
        user_msg = Message(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            sender_role=SenderRoles.USER,
            content=user_content,
            is_moderated=True,
            moderation_reason=reason
        )
        db.session.add(user_msg)
        
        # Salva a mensagem de *bloqueio* como se fosse da Amanda
        amanda_msg = Message(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            sender_role=SenderRoles.AMANDA,
            content=block_message_content, # (Aqui não é JSON, é a msg de bloqueio)
            is_moderated=True # Flag para o front saber
        )
        db.session.add(amanda_msg)
        db.session.commit()
        
        # Retorna a mensagem de bloqueio para o front
        return jsonify(amanda_msg.to_dict()), 403 # 403 Forbidden

    try:
        # 3. Se não for bloqueado: Salva a mensagem do usuário
        user_msg = Message(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            sender_role=SenderRoles.USER,
            content=user_content
        )
        db.session.add(user_msg)
        
        # 4. Busca o histórico de chat para dar contexto à IA
        history = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at.asc()).all()
        
        # 5. Chama a Amanda AI (Gemini)
        # O history já inclui a nova msg do usuário, o service sabe como lidar
        ai_response_json_string = AIService.generate_response(history, user_content)
        
        # 6. Salva a resposta da IA
        # O AIService retorna um JSON *como string*
        amanda_msg = Message(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            sender_role=SenderRoles.AMANDA,
            content=ai_response_json_string
        )
        db.session.add(amanda_msg)
        
        # 7. Confirma tudo no banco
        db.session.commit()
        
        # 8. Retorna a resposta da IA (como um objeto JSON) para o frontend
        # (O frontend espera o JSON estruturado)
        return jsonify(json.loads(ai_response_json_string)), 200

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao enviar mensagem: {e}")
        return jsonify({"error": "Erro interno ao processar a mensagem."}), 500

@chat_bp.route('/history/<string:chat_id>', methods=['GET'])
@jwt_required()
def get_chat_history(chat_id):
    """
    Retorna o histórico completo de um chat.
    """
    user_id = get_user_identity()
    chat = Chat.query.get(chat_id)
    user = User.query.get(user_id)

    if not chat:
        return jsonify({"error": "Chat não encontrado."}), 404
    if chat.user_id != user_id and user.role.permission_level > Cargos.HELPER_N3:
        return jsonify({"error": "Acesso negado a este chat."}), 403
        
    try:
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at.asc()).all()
        
        # Transforma as mensagens em dicionários
        # O frontend.js precisará fazer json.loads() no 'content'
        # se o sender_role for 'amanda'
        history_list = [msg.to_dict() for msg in messages]
        
        return jsonify(history_list), 200
        
    except Exception as e:
        print(f"Erro ao buscar histórico: {e}")
        return jsonify({"error": "Erro interno ao buscar histórico."}), 500