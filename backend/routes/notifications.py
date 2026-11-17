"""Endpoint notifikasi dalam aplikasi."""

from flask import Blueprint, g, jsonify, request

from middleware.auth import token_required
from services import notification_service
from utils.pagination import get_pagination_args, pagination_meta
from utils.request_utils import get_optional_json_body

notifications_bp = Blueprint("notifications", __name__)


def _summary_key(user):
    return notification_service.notification_summary(user)


@notifications_bp.get("/notifications")
@token_required
def list_notifications():
    page, per_page = get_pagination_args()
    items, pagination = notification_service.list_notifications(
        g.current_user, page=page, per_page=per_page
    )
    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "items": items,
                    "pagination": pagination_meta(pagination),
                    "unread_count": _summary_key(g.current_user)["unread_count"],
                },
            }
        ),
        200,
    )


@notifications_bp.get("/notifications/unread-count")
@token_required
def get_unread_count():
    return (
        jsonify({"success": True, "data": _summary_key(g.current_user)}),
        200,
    )


@notifications_bp.patch("/notifications/read")
@token_required
def mark_read():
    data = get_optional_json_body() or {}
    ids = data.get("ids", [])
    updated = notification_service.mark_read(g.current_user, ids)
    return (
        jsonify(
            {
                "success": True,
                "message": "Notifikasi ditandai sudah dibaca.",
                "data": {**updated, "unread_count": _summary_key(g.current_user)["unread_count"]},
            }
        ),
        200,
    )


@notifications_bp.post("/notifications/read-all")
@token_required
def mark_all_read():
    updated = notification_service.mark_all_read(g.current_user)
    return (
        jsonify(
            {
                "success": True,
                "message": "Semua notifikasi ditandai sudah dibaca.",
                "data": {**updated, "unread_count": _summary_key(g.current_user)["unread_count"]},
            }
        ),
        200,
    )
