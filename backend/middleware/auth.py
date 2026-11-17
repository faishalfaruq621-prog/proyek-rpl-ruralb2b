"""Middleware autentikasi JWT."""

from functools import wraps

import jwt
from flask import g, request

from extensions import db
from models import User
from utils.api_error import ApiError
from utils.jwt_utils import decode_access_token
from utils.token_blocklist import is_token_revoked


def token_required(view):
    """Memastikan request memiliki Bearer token yang valid dan aktif."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        authorization = request.headers.get("Authorization", "").strip()
        parts = authorization.split()

        if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
            raise ApiError(
                "Token autentikasi tidak ditemukan. Gunakan header "
                "Authorization: Bearer <token>.",
                status_code=401,
                code="token_missing",
            )

        token = parts[1]

        try:
            payload = decode_access_token(token)
        except jwt.ExpiredSignatureError as exc:
            raise ApiError(
                "Token sudah kedaluwarsa. Silakan login kembali.",
                status_code=401,
                code="token_expired",
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise ApiError(
                "Token tidak valid.",
                status_code=401,
                code="token_invalid",
            ) from exc

        if payload.get("type") != "access":
            raise ApiError(
                "Jenis token tidak didukung.",
                status_code=401,
                code="token_invalid_type",
            )

        jti = payload.get("jti")
        if not jti:
            raise ApiError(
                "Token tidak valid.",
                status_code=401,
                code="token_invalid",
            )

        if is_token_revoked(jti):
            raise ApiError(
                "Token sudah digunakan untuk logout. Silakan login kembali.",
                status_code=401,
                code="token_revoked",
            )

        try:
            user_id = int(payload.get("sub", ""))
        except (TypeError, ValueError) as exc:
            raise ApiError(
                "Token tidak valid.",
                status_code=401,
                code="token_invalid",
            ) from exc

        user = db.session.get(User, user_id)
        if user is None:
            raise ApiError(
                "Pengguna tidak ditemukan.",
                status_code=401,
                code="user_not_found",
            )

        if user.account_status == "suspended":
            raise ApiError(
                "Akun Anda ditangguhkan. Hubungi administrator.",
                status_code=403,
                code="account_suspended",
            )

        if user.account_status != "active":
            raise ApiError(
                "Akun Anda tidak aktif. Hubungi administrator.",
                status_code=403,
                code="account_inactive",
            )

        g.current_user = user
        g.jwt_payload = payload
        g.jwt_token = token

        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    """Membatasi endpoint hanya untuk pengguna dengan role admin.

    Decorator ini membungkus ``token_required`` sehingga token tetap
    diverifikasi terlebih dahulu.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if user is None:
            raise ApiError(
                "Token autentikasi tidak ditemukan.",
                status_code=401,
                code="token_missing",
            )
        if user.role != "admin":
            raise ApiError(
                "Akses ditolak. Endpoint ini hanya untuk admin.",
                status_code=403,
                code="admin_required",
            )
        return view(*args, **kwargs)

    return token_required(wrapped)


def business_user_required(view):
    """Membatasi endpoint pengelolaan produk hanya untuk business user."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if user is None:
            raise ApiError(
                "Token autentikasi tidak ditemukan.",
                status_code=401,
                code="token_missing",
            )
        if user.role != "business_user":
            raise ApiError(
                "Akses ditolak. Endpoint ini hanya untuk pengguna bisnis.",
                status_code=403,
                code="business_user_required",
            )
        return view(*args, **kwargs)

    return token_required(wrapped)
