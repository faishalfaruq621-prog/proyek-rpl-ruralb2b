"""Endpoint keranjang belanja pembeli."""

from flask import Blueprint, g, jsonify

from middleware.auth import business_user_required
from services.cart_service import (
    add_cart_item,
    delete_cart_item,
    get_cart,
    update_cart_item,
)
from utils.request_utils import get_json_body

cart_bp = Blueprint("cart", __name__)


@cart_bp.get("/cart")
@business_user_required
def get_cart_route():
    return (
        jsonify(
            {
                "success": True,
                "data": {"cart": get_cart(g.current_user)},
            }
        ),
        200,
    )


@cart_bp.post("/cart/items")
@business_user_required
def add_cart_item_route():
    cart = add_cart_item(g.current_user, get_json_body())
    return (
        jsonify(
            {
                "success": True,
                "message": "Produk berhasil ditambahkan ke keranjang.",
                "data": {"cart": cart},
            }
        ),
        201,
    )


@cart_bp.patch("/cart/items/<int:item_id>")
@business_user_required
def update_cart_item_route(item_id: int):
    cart = update_cart_item(g.current_user, item_id, get_json_body())
    return (
        jsonify(
            {
                "success": True,
                "message": "Jumlah produk di keranjang berhasil diperbarui.",
                "data": {"cart": cart},
            }
        ),
        200,
    )


@cart_bp.delete("/cart/items/<int:item_id>")
@business_user_required
def delete_cart_item_route(item_id: int):
    cart = delete_cart_item(g.current_user, item_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Produk berhasil dihapus dari keranjang.",
                "data": {"cart": cart},
            }
        ),
        200,
    )
