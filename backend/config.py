"""Konfigurasi aplikasi RuralB2B.

Semua nilai sensitif dibaca dari file .env. Jangan menaruh kredensial
database atau secret key langsung di dalam kode.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Nilai {name} harus berupa angka.") from exc


def _get_cors_origins() -> str | list[str]:
    raw = os.getenv("CORS_ORIGINS", "*")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if not origins or origins == ["*"]:
        return "*"
    return origins


class Config:
    """Konfigurasi default untuk seluruh environment."""

    # --- Database (MySQL Laragon) ---
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "ruralb2b")
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    SQLALCHEMY_DATABASE_URI = URL.create(
        drivername="mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD or None,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
        query={"charset": "utf8mb4"},
    ).render_as_string(hide_password=False)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # --- JWT ---
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRES_MINUTES = _get_int("JWT_EXPIRES_MINUTES", 60)
    JWT_ISSUER = os.getenv("JWT_ISSUER", "ruralb2b-api")
    JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "ruralb2b-client")

    # --- Flask / CORS ---
    SECRET_KEY = JWT_SECRET_KEY
    DEBUG = _get_bool("FLASK_DEBUG", False)
    CORS_ORIGINS = _get_cors_origins()

    # --- Upload dokumen verifikasi ---
    VERIFICATION_UPLOAD_DIR = os.getenv(
        "VERIFICATION_UPLOAD_DIR", ""
    ).strip() or str(BASE_DIR / "storage" / "verification_documents")
    MAX_VERIFICATION_DOCUMENT_SIZE = _get_int(
        "MAX_VERIFICATION_DOCUMENT_SIZE", 5 * 1024 * 1024
    )
    MAX_VERIFICATION_DOCUMENTS = _get_int("MAX_VERIFICATION_DOCUMENTS", 10)

    # --- Upload gambar produk ---
    PRODUCT_IMAGE_UPLOAD_DIR = os.getenv(
        "PRODUCT_IMAGE_UPLOAD_DIR", ""
    ).strip() or str(BASE_DIR / "storage" / "product_images")
    MAX_PRODUCT_IMAGE_SIZE = _get_int(
        "MAX_PRODUCT_IMAGE_SIZE", 5 * 1024 * 1024
    )
    MAX_PRODUCT_IMAGES = _get_int("MAX_PRODUCT_IMAGES", 5)

    # --- Upload bukti pembayaran ---
    PAYMENT_PROOF_UPLOAD_DIR = os.getenv(
        "PAYMENT_PROOF_UPLOAD_DIR", ""
    ).strip() or str(BASE_DIR / "storage" / "payment_proofs")
    MAX_PAYMENT_PROOF_SIZE = _get_int(
        "MAX_PAYMENT_PROOF_SIZE", 5 * 1024 * 1024
    )

    MAX_CONTENT_LENGTH = _get_int("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)

    # --- Telegram Bot API ---
    # TELEGRAM_CHAT_ID adalah alias dari TELEGRAM_ADMIN_CHAT_ID agar
    # konfigurasi dengan salah satu penamaan tetap berfungsi.
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    TELEGRAM_ADMIN_CHAT_ID = (
        os.getenv("TELEGRAM_ADMIN_CHAT_ID", "").strip()
        or os.getenv("TELEGRAM_CHAT_ID", "").strip()
    )
    TELEGRAM_API_TIMEOUT = _get_int("TELEGRAM_API_TIMEOUT", 5)

    # --- AI Integration Configuration ---
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip()
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "").strip()
    AI_DAILY_LIMIT = _get_int("AI_DAILY_LIMIT", 50)
    AI_REQUEST_TIMEOUT = _get_int("AI_REQUEST_TIMEOUT", 30)
