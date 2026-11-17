"""Endpoint katalog publik dan pengelolaan produk oleh penjual."""

from flask import Blueprint, g, jsonify, request, send_file

from middleware.auth import business_user_required
from services.product_service import (
    add_product_image,
    create_product,
    delete_product,
    delete_product_image_record,
    get_public_image_file,
    get_public_product,
    list_categories,
    list_public_products,
    update_product,
)
from utils.api_error import ApiError
from utils.pagination import get_pagination_args, pagination_meta
from utils.product_validators import validate_positive_int_filter
from utils.request_utils import get_json_body

products_bp = Blueprint("products", __name__)


@products_bp.get("/products")
def public_product_list():
    page, per_page = get_pagination_args()
    items, pagination = list_public_products(
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


@products_bp.get("/products/<int:product_id>")
def public_product_detail(product_id: int):
    return (
        jsonify(
            {
                "success": True,
                "data": {"product": get_public_product(product_id)},
            }
        ),
        200,
    )


@products_bp.get("/categories")
def public_category_list():
    parent_id = validate_positive_int_filter(
        request.args.get("parent_id"), "parent_id", "Parent kategori"
    )
    return (
        jsonify(
            {
                "success": True,
                "data": {"items": list_categories(parent_id=parent_id)},
            }
        ),
        200,
    )


@products_bp.get("/products/<int:product_id>/images/<int:image_id>/file")
def public_product_image(product_id: int, image_id: int):
    path, download_name, mimetype = get_public_image_file(
        product_id, image_id
    )
    return send_file(
        path,
        mimetype=mimetype,
        download_name=download_name,
        conditional=True,
    )


@products_bp.post("/products")
@business_user_required
def create_product_route():
    product = create_product(g.current_user, get_json_body())
    return (
        jsonify(
            {
                "success": True,
                "message": "Produk berhasil dibuat.",
                "data": {"product": product},
            }
        ),
        201,
    )


@products_bp.put("/products/<int:product_id>")
@business_user_required
def replace_product_route(product_id: int):
    product = update_product(
        g.current_user, product_id, get_json_body(), partial=False
    )
    return (
        jsonify(
            {
                "success": True,
                "message": "Produk berhasil diperbarui.",
                "data": {"product": product},
            }
        ),
        200,
    )


@products_bp.patch("/products/<int:product_id>")
@business_user_required
def patch_product_route(product_id: int):
    product = update_product(
        g.current_user, product_id, get_json_body(), partial=True
    )
    return (
        jsonify(
            {
                "success": True,
                "message": "Produk berhasil diperbarui.",
                "data": {"product": product},
            }
        ),
        200,
    )


@products_bp.delete("/products/<int:product_id>")
@business_user_required
def delete_product_route(product_id: int):
    delete_product(g.current_user, product_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Produk berhasil dihapus.",
            }
        ),
        200,
    )


@products_bp.post("/products/<int:product_id>/images")
@business_user_required
def upload_product_image_route(product_id: int):
    if "file" not in request.files:
        raise ApiError(
            "File gambar wajib diunggah.",
            status_code=422,
            errors={
                "file": "Gunakan multipart/form-data dengan field 'file'."
            },
            code="file_required",
        )

    file_storage = request.files["file"]
    if not file_storage.filename:
        raise ApiError(
            "Nama file tidak valid.",
            status_code=422,
            errors={"file": "Pilih gambar yang akan diunggah."},
            code="file_required",
        )

    image = add_product_image(
        g.current_user,
        product_id,
        file_storage,
        request.form.get("is_primary"),
    )
    return (
        jsonify(
            {
                "success": True,
                "message": "Gambar produk berhasil diunggah.",
                "data": {"image": image},
            }
        ),
        201,
    )


@products_bp.delete("/products/<int:product_id>/images/<int:image_id>")
@business_user_required
def delete_product_image_route(product_id: int, image_id: int):
    delete_product_image_record(g.current_user, product_id, image_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Gambar produk berhasil dihapus.",
            }
        ),
        200,
    )
