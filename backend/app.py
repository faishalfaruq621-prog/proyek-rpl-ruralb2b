"""Entry point aplikasi RuralB2B.

Menjalankan backend:
    python app.py

Semua konfigurasi sensitif dibaca dari backend/.env.
"""

import os
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

import models  # noqa: F401  (memastikan model terdaftar pada metadata SQLAlchemy)
from config import Config
from extensions import db
from routes.admin import admin_bp
from routes.ai import ai_bp
from routes.chat import chat_bp
from routes.notifications import notifications_bp
from routes.auth import auth_bp
from routes.business import business_bp
from routes.cart import cart_bp
from routes.orders import orders_bp
from routes.products import products_bp
from utils.api_error import ApiError


def _prepare_private_storage(app: Flask, config_key: str, label: str) -> None:
    """Menyiapkan direktori privat dan memastikan tidak berada di static."""

    upload_setting = Path(app.config[config_key])
    if not upload_setting.is_absolute():
        upload_setting = Path(app.root_path) / upload_setting
    upload_dir = upload_setting.expanduser().resolve()

    static_folder = app.static_folder
    if static_folder:
        static_dir = Path(static_folder).resolve()
        if upload_dir == static_dir or static_dir in upload_dir.parents:
            raise RuntimeError(
                f"{config_key} tidak boleh berada di dalam "
                "direktori publik/static."
            )

    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Direktori penyimpanan {label} tidak dapat dibuat."
        ) from exc

    app.config[config_key] = str(upload_dir)


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError(
            "JWT_SECRET_KEY belum diatur. Tambahkan nilai acak pada backend/.env."
        )

    if not app.config.get("DB_USER"):
        raise RuntimeError("DB_USER belum diatur pada backend/.env.")

    if not app.config.get("DB_NAME"):
        raise RuntimeError("DB_NAME belum diatur pada backend/.env.")

    if (
        len(app.config["JWT_SECRET_KEY"]) < 32
        or app.config["JWT_SECRET_KEY"]
        == "ganti-dengan-secret-acak-yang-panjang"
    ):
        raise RuntimeError(
            "JWT_SECRET_KEY minimal 32 karakter dan tidak boleh memakai nilai contoh."
        )

    if app.config["JWT_EXPIRES_MINUTES"] <= 0:
        raise RuntimeError("JWT_EXPIRES_MINUTES harus lebih besar dari 0.")

    if app.config["JWT_ALGORITHM"] not in {"HS256", "HS384", "HS512"}:
        raise RuntimeError(
            "JWT_ALGORITHM harus salah satu dari HS256, HS384, atau HS512."
        )

    if app.config["MAX_VERIFICATION_DOCUMENT_SIZE"] <= 0:
        raise RuntimeError(
            "MAX_VERIFICATION_DOCUMENT_SIZE harus lebih besar dari 0."
        )

    if app.config["MAX_VERIFICATION_DOCUMENTS"] <= 0:
        raise RuntimeError("MAX_VERIFICATION_DOCUMENTS harus lebih besar dari 0.")

    if app.config["MAX_PRODUCT_IMAGE_SIZE"] <= 0:
        raise RuntimeError("MAX_PRODUCT_IMAGE_SIZE harus lebih besar dari 0.")

    if app.config["MAX_PRODUCT_IMAGES"] <= 0:
        raise RuntimeError("MAX_PRODUCT_IMAGES harus lebih besar dari 0.")

    if app.config["MAX_PAYMENT_PROOF_SIZE"] <= 0:
        raise RuntimeError("MAX_PAYMENT_PROOF_SIZE harus lebih besar dari 0.")

    largest_upload = max(
        app.config["MAX_VERIFICATION_DOCUMENT_SIZE"],
        app.config["MAX_PRODUCT_IMAGE_SIZE"],
        app.config["MAX_PAYMENT_PROOF_SIZE"],
    )
    if app.config["MAX_CONTENT_LENGTH"] < largest_upload:
        raise RuntimeError(
            "MAX_CONTENT_LENGTH tidak boleh lebih kecil dari batas upload "
            "dokumen/gambar/bukti pembayaran."
        )

    if app.config["TELEGRAM_API_TIMEOUT"] <= 0:
        raise RuntimeError("TELEGRAM_API_TIMEOUT harus lebih besar dari 0.")

    _prepare_private_storage(
        app, "VERIFICATION_UPLOAD_DIR", "dokumen verifikasi"
    )
    _prepare_private_storage(app, "PRODUCT_IMAGE_UPLOAD_DIR", "gambar produk")
    _prepare_private_storage(
        app, "PAYMENT_PROOF_UPLOAD_DIR", "bukti pembayaran"
    )

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    db.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(business_bp, url_prefix="/api/business")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(products_bp, url_prefix="/api")
    app.register_blueprint(cart_bp, url_prefix="/api")
    app.register_blueprint(orders_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(notifications_bp, url_prefix="/api")

    @app.get("/")
    def home():
        return jsonify(
            {
                "app": "RuralB2B API",
                "status": "running",
                "version": "1.0.0",
                "message": "Backend berhasil dijalankan.",
            }
        )

    @app.get("/api/health")
    def health():
        try:
            with db.engine.connect() as connection:
                connection.exec_driver_sql("SELECT 1")
            return jsonify({"status": "ok", "database": "connected"}), 200
        except Exception:
            app.logger.exception("Pemeriksaan koneksi database gagal")
            return (
                jsonify(
                    {
                        "status": "error",
                        "database": "disconnected",
                        "message": "Koneksi database gagal.",
                    }
                ),
                503,
            )

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Endpoint tidak ditemukan.",
                    "code": "not_found",
                }
            ),
            404,
        )

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Metode HTTP tidak diizinkan untuk endpoint ini.",
                    "code": "method_not_allowed",
                }
            ),
            405,
        )

    @app.errorhandler(413)
    def handle_request_too_large(error):
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Ukuran request terlalu besar.",
                    "code": "request_too_large",
                    "details": {
                        "max_size_bytes": app.config["MAX_CONTENT_LENGTH"]
                    },
                }
            ),
            413,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": error.description,
                        "code": error.name.lower().replace(" ", "_"),
                    }
                ),
                error.code,
            )

        db.session.rollback()
        app.logger.error("Terjadi kesalahan tak terduga", exc_info=app.debug)
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Terjadi kesalahan pada server.",
                    "code": "internal_server_error",
                }
            ),
            500,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=app.config["DEBUG"],
    )
