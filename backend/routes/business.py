"""Endpoint profil bisnis, verifikasi, produk, dan inventori penjual."""

from flask import Blueprint, g, jsonify, request, send_file

from middleware.auth import business_user_required, token_required
from services.business_profile_service import (
    build_profile_payload,
    update_profile,
)
from services.product_service import (
    get_business_image_file,
    get_business_product,
    list_business_inventory,
    list_business_products,
    update_inventory,
)
from services.verification_service import (
    create_verification,
    get_document_file_for_user,
    get_user_verification,
    list_user_verifications,
    upload_document,
)
from utils.api_error import ApiError
from utils.pagination import get_pagination_args, pagination_meta
from utils.request_utils import get_json_body

business_bp = Blueprint("business", __name__)


@business_bp.get("/profile")
@token_required
def get_profile():
    return (
        jsonify(
            {
                "success": True,
                "data": build_profile_payload(g.current_user),
            }
        ),
        200,
    )


@business_bp.put("/profile")
@token_required
def replace_profile():
    data = get_json_body()
    payload = update_profile(g.current_user, data, partial=False)
    return (
        jsonify(
            {
                "success": True,
                "message": "Profil bisnis berhasil diperbarui.",
                "data": payload,
            }
        ),
        200,
    )


@business_bp.patch("/profile")
@token_required
def patch_profile():
    data = get_json_body()
    payload = update_profile(g.current_user, data, partial=True)
    return (
        jsonify(
            {
                "success": True,
                "message": "Profil bisnis berhasil diperbarui.",
                "data": payload,
            }
        ),
        200,
    )


@business_bp.get("/verifications")
@token_required
def list_verifications():
    page, per_page = get_pagination_args()
    items, pagination = list_user_verifications(
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


@business_bp.post("/verifications")
@token_required
def submit_verification():
    # Pengajuan tidak membutuhkan body; dokumen diunggah lewat endpoint
    # dokumen setelah pengajuan dibuat.
    get_json_body(required=False)
    payload, notification = create_verification(g.current_user)
    payload["notification"] = notification
    return (
        jsonify(
            {
                "success": True,
                "message": "Pengajuan verifikasi berhasil dibuat.",
                "data": payload,
            }
        ),
        201,
    )


@business_bp.get("/verifications/<int:verification_id>")
@token_required
def get_verification(verification_id: int):
    return (
        jsonify(
            {
                "success": True,
                "data": get_user_verification(
                    g.current_user, verification_id
                ),
            }
        ),
        200,
    )


@business_bp.post("/verifications/<int:verification_id>/documents")
@token_required
def add_verification_document(verification_id: int):
    if "file" not in request.files:
        raise ApiError(
            "File dokumen wajib diunggah.",
            status_code=422,
            errors={"file": "Gunakan multipart/form-data dengan field 'file'."},
            code="file_required",
        )

    file_storage = request.files["file"]
    if not file_storage.filename:
        raise ApiError(
            "Nama file tidak valid.",
            status_code=422,
            errors={"file": "Pilih file yang akan diunggah."},
            code="file_required",
        )

    document = upload_document(
        g.current_user,
        verification_id,
        request.form.get("document_type"),
        file_storage,
    )
    return (
        jsonify(
            {
                "success": True,
                "message": "Dokumen berhasil diunggah.",
                "data": {"document": document},
            }
        ),
        201,
    )


@business_bp.get(
    "/verifications/<int:verification_id>/documents/<int:document_id>/download"
)
@token_required
def download_verification_document(verification_id: int, document_id: int):
    path, download_name, mimetype = get_document_file_for_user(
        g.current_user, verification_id, document_id
    )
    return send_file(
        path,
        as_attachment=True,
        download_name=download_name,
        mimetype=mimetype,
    )


@business_bp.get("/products")
@business_user_required
def list_own_products():
    page, per_page = get_pagination_args()
    items, pagination = list_business_products(
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


@business_bp.get("/products/<int:product_id>")
@business_user_required
def get_own_product(product_id: int):
    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "product": get_business_product(
                        g.current_user, product_id
                    )
                },
            }
        ),
        200,
    )


@business_bp.get(
    "/products/<int:product_id>/images/<int:image_id>/file"
)
@business_user_required
def get_own_product_image(product_id: int, image_id: int):
    path, download_name, mimetype = get_business_image_file(
        g.current_user, product_id, image_id
    )
    return send_file(
        path,
        mimetype=mimetype,
        download_name=download_name,
        conditional=True,
    )


@business_bp.get("/inventory")
@business_user_required
def list_own_inventory():
    page, per_page = get_pagination_args()
    items, pagination = list_business_inventory(
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


@business_bp.patch("/inventory/<int:product_id>")
@business_user_required
def patch_own_inventory(product_id: int):
    payload = update_inventory(
        g.current_user, product_id, get_json_body()
    )
    return (
        jsonify(
            {
                "success": True,
                "message": "Stok produk berhasil diperbarui.",
                "data": payload,
            }
        ),
        200,
    )
