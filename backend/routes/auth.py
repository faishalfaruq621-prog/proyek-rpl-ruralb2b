"""Endpoint autentikasi RuralB2B."""

from flask import Blueprint, g, jsonify, request

from middleware.auth import token_required
from services.auth_service import login_user, register_user
from utils.api_error import ApiError
from utils.token_blocklist import revoke_token

auth_bp = Blueprint("auth", __name__)


def _get_json_body() -> dict:
    if not request.is_json:
        raise ApiError(
            "Content-Type harus application/json.",
            status_code=415,
            code="unsupported_media_type",
        )

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(
            "Body request harus berupa objek JSON yang valid.",
            status_code=400,
            code="invalid_json",
        )

    return data


@auth_bp.post("/register")
def register():
    data = _get_json_body()
    user = register_user(data)

    return (
        jsonify(
            {
                "success": True,
                "message": "Registrasi berhasil. Silakan login untuk mendapatkan token.",
                "data": {"user": user.to_dict()},
            }
        ),
        201,
    )


@auth_bp.post("/login")
def login():
    data = _get_json_body()
    result = login_user(data)

    return (
        jsonify(
            {
                "success": True,
                "message": "Login berhasil.",
                "data": result,
            }
        ),
        200,
    )


@auth_bp.post("/logout")
@token_required
def logout():
    payload = g.jwt_payload
    revoke_token(payload["jti"], payload["exp"])

    return (
        jsonify(
            {
                "success": True,
                "message": "Logout berhasil. Token tidak dapat digunakan lagi.",
            }
        ),
        200,
    )


@auth_bp.post("/change-password")
@token_required
def change_password():
    from extensions import db
    from services.auth_service import validate_change_password_payload

    data = _get_json_body()
    values = validate_change_password_payload(data)

    user = g.current_user
    if not user.check_password(values["current_password"]):
        raise ApiError(
            "Password saat ini tidak benar.",
            status_code=401,
            code="current_password_mismatch",
        )
    if values["current_password"] == values["new_password"]:
        raise ApiError(
            "Password baru tidak boleh sama dengan password saat ini.",
            status_code=422,
            errors={"new_password": "Password baru harus berbeda."},
        )

    user.set_password(values["new_password"])
    db.session.commit()

    return (
        jsonify(
            {
                "success": True,
                "message": "Password berhasil diubah.",
            }
        ),
        200,
    )


@auth_bp.get("/me")
@token_required
def me():
    return (
        jsonify(
            {
                "success": True,
                "data": {"user": g.current_user.to_dict()},
            }
        ),
        200,
    )
