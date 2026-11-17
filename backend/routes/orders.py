"""Endpoint pesanan pembeli dan pengelolaan pesanan oleh penjual."""

from flask import Blueprint, g, jsonify, request, send_file

from middleware.auth import business_user_required
from services.order_service import (
    cancel_order,
    checkout,
    get_buyer_order,
    get_seller_order,
    list_buyer_orders,
    list_seller_orders,
    receive_order,
    update_order_status,
)
from services.payment_service import (
    confirm_payment,
    get_buyer_payment,
    get_buyer_payment_proof,
    get_seller_payment_proof,
    submit_payment,
    upload_payment_proof,
)
from utils.api_error import ApiError
from utils.pagination import get_pagination_args, pagination_meta
from utils.request_utils import get_json_body, get_optional_json_body

orders_bp = Blueprint("orders", __name__)


@orders_bp.post("/orders/checkout")
@business_user_required
def checkout_route():
    orders = checkout(g.current_user, get_json_body())
    return (
        jsonify(
            {
                "success": True,
                "message": "Checkout berhasil. Pesanan dipisahkan per penjual.",
                "data": {
                    "orders": orders,
                    "order_count": len(orders),
                },
            }
        ),
        201,
    )


@orders_bp.get("/orders")
@business_user_required
def buyer_order_list():
    page, per_page = get_pagination_args()
    items, pagination = list_buyer_orders(
        g.current_user, request.args, page=page, per_page=per_page
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


@orders_bp.get("/orders/<int:order_id>")
@business_user_required
def buyer_order_detail(order_id: int):
    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "order": get_buyer_order(g.current_user, order_id)
                },
            }
        ),
        200,
    )


@orders_bp.post("/orders/<int:order_id>/cancel")
@business_user_required
def buyer_cancel_order(order_id: int):
    order = cancel_order(
        g.current_user, order_id, get_optional_json_body()
    )
    return (
        jsonify(
            {
                "success": True,
                "message": "Pesanan berhasil dibatalkan.",
                "data": {"order": order},
            }
        ),
        200,
    )


@orders_bp.post("/orders/<int:order_id>/receive")
@business_user_required
def buyer_receive_order(order_id: int):
    order = receive_order(g.current_user, order_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Pesanan dikonfirmasi diterima.",
                "data": {"order": order},
            }
        ),
        200,
    )


@orders_bp.get("/orders/<int:order_id>/payment")
@business_user_required
def buyer_order_payment(order_id: int):
    return (
        jsonify(
            {
                "success": True,
                "data": get_buyer_payment(g.current_user, order_id),
            }
        ),
        200,
    )


@orders_bp.patch("/orders/<int:order_id>/payment")
@business_user_required
def buyer_submit_payment(order_id: int):
    payload = submit_payment(
        g.current_user, order_id, get_json_body()
    )
    return (
        jsonify(
            {
                "success": True,
                "message": (
                    "Informasi pembayaran dikirim dan menunggu konfirmasi "
                    "penjual."
                ),
                "data": payload,
            }
        ),
        200,
    )


@orders_bp.post("/orders/<int:order_id>/payment/proof")
@business_user_required
def buyer_order_payment_proof_upload(order_id: int):
    if "file" not in request.files:
        raise ApiError(
            "File bukti pembayaran wajib diunggah.",
            status_code=422,
            errors={"file": "Gunakan multipart/form-data dengan field 'file'."},
            code="file_required",
        )

    file_storage = request.files["file"]
    if not file_storage.filename:
        raise ApiError(
            "Nama file bukti pembayaran tidak valid.",
            status_code=422,
            errors={"file": "Pilih file bukti pembayaran yang akan diunggah."},
            code="file_required",
        )

    payload = upload_payment_proof(
        g.current_user, order_id, file_storage
    )
    return (
        jsonify(
            {
                "success": True,
                "message": "Bukti pembayaran berhasil diunggah.",
                "data": payload,
            }
        ),
        201,
    )


@orders_bp.get("/orders/<int:order_id>/payment/proof/download")
@business_user_required
def buyer_order_payment_proof_download(order_id: int):
    path, download_name, mimetype = get_buyer_payment_proof(
        g.current_user, order_id
    )
    return send_file(
        path,
        as_attachment=True,
        download_name=download_name,
        mimetype=mimetype,
    )


@orders_bp.get("/seller/orders/<int:order_id>/payment/proof/download")
@business_user_required
def seller_order_payment_proof_download(order_id: int):
    path, download_name, mimetype = get_seller_payment_proof(
        g.current_user, order_id
    )
    return send_file(
        path,
        as_attachment=True,
        download_name=download_name,
        mimetype=mimetype,
    )


@orders_bp.get("/seller/orders")
@business_user_required
def seller_order_list():
    page, per_page = get_pagination_args()
    items, pagination = list_seller_orders(
        g.current_user, request.args, page=page, per_page=per_page
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


@orders_bp.get("/seller/orders/<int:order_id>")
@business_user_required
def seller_order_detail(order_id: int):
    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "order": get_seller_order(g.current_user, order_id)
                },
            }
        ),
        200,
    )


@orders_bp.patch("/seller/orders/<int:order_id>/status")
@business_user_required
def seller_update_order_status(order_id: int):
    order = update_order_status(
        g.current_user, order_id, get_json_body()
    )
    return (
        jsonify(
            {
                "success": True,
                "message": "Status pesanan berhasil diperbarui.",
                "data": {"order": order},
            }
        ),
        200,
    )


@orders_bp.post("/seller/orders/<int:order_id>/payment/confirm")
@business_user_required
def seller_confirm_payment(order_id: int):
    payload = confirm_payment(
        g.current_user, order_id, get_optional_json_body()
    )
    return (
        jsonify(
            {
                "success": True,
                "message": "Pembayaran berhasil dikonfirmasi.",
                "data": payload,
            }
        ),
        200,
    )
