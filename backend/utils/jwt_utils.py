"""Pembuatan dan verifikasi access token JWT."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from flask import current_app


def create_access_token(user) -> tuple[str, datetime, dict]:
    """Membuat access token untuk ``user``.

    Returns:
        tuple: (token, waktu_kedaluwarsa, payload)
    """

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=current_app.config["JWT_EXPIRES_MINUTES"])
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "type": "access",
        "jti": uuid4().hex,
        "iat": now,
        "nbf": now,
        "exp": expires_at,
        "iss": current_app.config["JWT_ISSUER"],
        "aud": current_app.config["JWT_AUDIENCE"],
    }
    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )
    return token, expires_at, payload


def decode_access_token(token: str) -> dict:
    """Memverifikasi signature, masa berlaku, issuer, dan audience token."""

    return jwt.decode(
        token,
        current_app.config["JWT_SECRET_KEY"],
        algorithms=[current_app.config["JWT_ALGORITHM"]],
        issuer=current_app.config["JWT_ISSUER"],
        audience=current_app.config["JWT_AUDIENCE"],
        options={"require": ["exp", "iat", "nbf", "sub", "jti", "iss", "aud"]},
    )
