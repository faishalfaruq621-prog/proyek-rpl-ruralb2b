"""Endpoint verifikasi untuk admin."""

from flask import Blueprint, g, jsonify, request, send_file

from middleware.auth import admin_required
from services import admin_service
from services.telegram_service import (
    admin_notification_logs,
    admin_send_test_message,
    admin_telegram_status,
    test_telegram_connection,
)
from services.verification_service import (
    admin_approve,
    admin_list_verifications,
    admin_logs,
    admin_reject,
    get_admin_verification,
    get_document_file_for_admin,
)
from utils.pagination import get_pagination_args, pagination_meta
from utils.request_utils import get_json_body

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/telegram/status")
@admin_required
def telegram_status():
    """Status integrasi Telegram (pemeriksaan aktual getMe, tanpa pesan)."""
    return jsonify({"success": True, "data": admin_telegram_status()}), 200


@admin_bp.post("/telegram/test-connection")
@admin_required
def telegram_test_connection():
    """Tes koneksi Bot API (getMe) — TIDAK mengirim pesan Telegram."""
    return jsonify({"success": True, "data": test_telegram_connection()}), 200


@admin_bp.post("/telegram/send-test-message")
@admin_required
def telegram_send_test_message():
    """Mengirim TEPAT SATU pesan tes (tanpa retry) ke chat admin."""
    return jsonify({"success": True, "data": admin_send_test_message()}), 200


@admin_bp.get("/telegram/logs")
@admin_required
def telegram_logs():
    """Riwayat pengiriman notifikasi Telegram (data aktual)."""
    limit = request.args.get("limit", default=20, type=int)
    if limit is None or limit <= 0 or limit > 100:
        limit = 20
    return (
        jsonify({"success": True, "data": {"items": admin_notification_logs(limit)}}),
        200,
    )


@admin_bp.get("/stats")
@admin_required
def stats():
    return jsonify({"success": True, "data": admin_service.admin_stats()}), 200


@admin_bp.get("/users")
@admin_required
def users():
    page, per_page = get_pagination_args()
    items, pagination = admin_service.list_users(
        request.args, page=page, per_page=per_page
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


@admin_bp.patch("/users/<int:user_id>")
@admin_required
def update_user(user_id: int):
    payload = admin_service.update_user(
        g.current_user, user_id, get_json_body()
    )
    return (
        jsonify(
            {
                "success": True,
                "message": "Data pengguna berhasil diperbarui.",
                "data": payload,
            }
        ),
        200,
    )


@admin_bp.get("/categories")
@admin_required
def list_categories():
    page, per_page = get_pagination_args()
    items, pagination = admin_service.list_categories_admin(
        page=page, per_page=per_page
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


@admin_bp.post("/categories")
@admin_required
def create_category():
    payload = admin_service.create_category(get_json_body())
    return (
        jsonify(
            {
                "success": True,
                "message": "Kategori berhasil dibuat.",
                "data": {"category": payload},
            }
        ),
        201,
    )


@admin_bp.patch("/categories/<int:category_id>")
@admin_required
def update_category(category_id: int):
    payload = admin_service.update_category(category_id, get_json_body())
    return (
        jsonify(
            {
                "success": True,
                "message": "Kategori berhasil diperbarui.",
                "data": {"category": payload},
            }
        ),
        200,
    )


@admin_bp.delete("/categories/<int:category_id>")
@admin_required
def delete_category(category_id: int):
    payload = admin_service.delete_category(category_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Kategori berhasil dihapus.",
                "data": payload,
            }
        ),
        200,
    )


@admin_bp.get("/orders")
@admin_required
def list_orders():
    page, per_page = get_pagination_args()
    items, pagination = admin_service.list_orders_admin(
        request.args, page=page, per_page=per_page
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


@admin_bp.get("/verifications")
@admin_required
def list_verifications():
    page, per_page = get_pagination_args()
    status = request.args.get("status")
    if status is not None:
        status = status.strip().lower() or None

    items, pagination = admin_list_verifications(
        status=status, page=page, per_page=per_page
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


@admin_bp.get("/verifications/<int:verification_id>")
@admin_required
def get_verification(verification_id: int):
    return (
        jsonify(
            {
                "success": True,
                "data": get_admin_verification(verification_id),
            }
        ),
        200,
    )


@admin_bp.post("/verifications/<int:verification_id>/approve")
@admin_required
def approve_verification(verification_id: int):
    data = get_json_body(required=False)
    payload, telegram = admin_approve(g.current_user, verification_id, data)
    return (
        jsonify(
            {
                "success": True,
                "message": "Pengajuan verifikasi disetujui.",
                "data": payload,
                "telegram": telegram,
            }
        ),
        200,
    )


@admin_bp.post("/verifications/<int:verification_id>/reject")
@admin_required
def reject_verification(verification_id: int):
    data = get_json_body(required=True)
    payload, telegram = admin_reject(g.current_user, verification_id, data)
    return (
        jsonify(
            {
                "success": True,
                "message": "Pengajuan verifikasi ditolak.",
                "data": payload,
                "telegram": telegram,
            }
        ),
        200,
    )


@admin_bp.get("/verifications/<int:verification_id>/logs")
@admin_required
def get_verification_logs(verification_id: int):
    return (
        jsonify(
            {
                "success": True,
                "data": {"items": admin_logs(verification_id)},
            }
        ),
        200,
    )


@admin_bp.get(
    "/verifications/<int:verification_id>/documents/<int:document_id>/download"
)
@admin_required
def download_verification_document(verification_id: int, document_id: int):
    path, download_name, mimetype = get_document_file_for_admin(
        verification_id, document_id
    )
    return send_file(
        path,
        as_attachment=True,
        download_name=download_name,
        mimetype=mimetype,
    )
