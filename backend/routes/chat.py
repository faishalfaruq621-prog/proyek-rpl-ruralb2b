"""Endpoint chat Buyer-Seller."""

from flask import Blueprint, g, jsonify

from middleware.auth import token_required
from services import chat_service
from utils.pagination import get_pagination_args, pagination_meta
from utils.request_utils import get_json_body

chat_bp = Blueprint("chat", __name__)


@chat_bp.post("/chat/conversations")
@token_required
def start_conversation():
    payload = chat_service.start_or_get_conversation(g.current_user, get_json_body())
    return (
        jsonify(
            {
                "success": True,
                "message": "Percakapan siap digunakan.",
                "data": {"conversation": payload},
            }
        ),
        200,
    )


@chat_bp.get("/chat/conversations")
@token_required
def list_conversations():
    page, per_page = get_pagination_args()
    items, pagination = chat_service.list_conversations(
        g.current_user, page=page, per_page=per_page
    )
    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "items": items,
                    "pagination": pagination_meta(pagination),
                },
            }
        ),
        200,
    )


@chat_bp.get("/chat/conversations/<int:conversation_id>")
@token_required
def get_conversation(conversation_id: int):
    payload = chat_service.get_conversation(g.current_user, conversation_id)
    return (
        jsonify({"success": True, "data": {"conversation": payload}}),
        200,
    )


@chat_bp.get("/chat/conversations/<int:conversation_id>/messages")
@token_required
def get_messages(conversation_id: int):
    page, per_page = get_pagination_args()
    items, pagination = chat_service.get_messages(
        g.current_user, conversation_id, page=page, per_page=per_page
    )
    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "items": items,
                    "pagination": pagination_meta(pagination),
                },
            }
        ),
        200,
    )


@chat_bp.post("/chat/conversations/<int:conversation_id>/messages")
@token_required
def send_message(conversation_id: int):
    payload = chat_service.send_message(
        g.current_user, conversation_id, get_json_body()
    )
    return (
        jsonify(
            {
                "success": True,
                "message": "Pesan terkirim.",
                "data": {"message": payload},
            }
        ),
        201,
    )
