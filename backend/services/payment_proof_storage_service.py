"""Penyimpanan bukti pembayaran di luar direktori publik."""

from pathlib import Path
from uuid import uuid4

from flask import current_app

from utils.api_error import ApiError

PAYMENT_PROOF_ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}

_PAYMENT_PROOF_MIME_BY_EXTENSION = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}


def _storage_root() -> Path:
    root = Path(current_app.config["PAYMENT_PROOF_UPLOAD_DIR"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _detect_payment_proof_type(head: bytes) -> str | None:
    if head.startswith(b"%PDF-"):
        return "pdf"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    return None


def payment_proof_mimetype(file_path: str) -> str:
    extension = Path(file_path).suffix.lower().lstrip(".")
    return _PAYMENT_PROOF_MIME_BY_EXTENSION.get(
        extension, "application/octet-stream"
    )


def safe_payment_proof_download_name(order_id: int, file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    return f"payment_{int(order_id)}{suffix}"


def save_payment_proof(file_storage, order_id: int) -> str:
    """Memvalidasi dan menyimpan bukti pembayaran dengan UUID."""

    original_name = getattr(file_storage, "filename", "") or ""
    extension = Path(original_name).suffix.lower().lstrip(".")

    if extension not in PAYMENT_PROOF_ALLOWED_EXTENSIONS:
        raise ApiError(
            "Jenis file bukti pembayaran tidak diizinkan.",
            status_code=422,
            errors={
                "file": "Gunakan file PDF, JPG, JPEG, atau PNG."
            },
            code="invalid_file_type",
        )

    max_size = int(current_app.config["MAX_PAYMENT_PROOF_SIZE"])

    try:
        data = file_storage.stream.read(max_size + 1)
    except OSError as exc:
        raise ApiError(
            "Bukti pembayaran tidak dapat dibaca.",
            status_code=400,
            errors={"file": "Pastikan bukti pembayaran tidak rusak."},
            code="file_read_error",
        ) from exc

    if not data:
        raise ApiError(
            "Bukti pembayaran kosong.",
            status_code=422,
            errors={
                "file": "Bukti pembayaran tidak boleh kosong."
            },
            code="empty_file",
        )

    if len(data) > max_size:
        raise ApiError(
            "Ukuran bukti pembayaran terlalu besar.",
            status_code=413,
            errors={
                "file": f"Ukuran maksimal {max_size // (1024 * 1024)} MB."
            },
            code="file_too_large",
            details={"max_size_bytes": max_size},
        )

    expected_type = "jpeg" if extension in {"jpg", "jpeg"} else extension
    detected_type = _detect_payment_proof_type(data[:16])

    if detected_type != expected_type:
        raise ApiError(
            "Isi file bukti pembayaran tidak sesuai dengan ekstensinya.",
            status_code=422,
            errors={
                "file": "Bukti pembayaran harus benar-benar berupa PDF, JPG, "
                "JPEG, atau PNG."
            },
            code="invalid_file_content",
        )

    root = _storage_root()
    absolute_dir = root / f"order_{int(order_id)}"

    try:
        absolute_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{uuid4().hex}.{extension}"
        absolute_path = absolute_dir / file_name
        absolute_path.write_bytes(data)
    except OSError as exc:
        raise ApiError(
            "Bukti pembayaran gagal disimpan.",
            status_code=500,
            code="storage_error",
        ) from exc

    return absolute_path.relative_to(root).as_posix()


def resolve_payment_proof(relative_path: str):
    """Mengembalikan path absolut aman untuk bukti pembayaran."""

    if not relative_path:
        raise ApiError(
            "Bukti pembayaran tidak ditemukan.",
            status_code=404,
            code="payment_proof_file_not_found",
        )

    root = _storage_root()
    try:
        candidate = (root / relative_path).resolve()
    except (OSError, RuntimeError) as exc:
        raise ApiError(
            "Bukti pembayaran tidak ditemukan.",
            status_code=404,
            code="payment_proof_file_not_found",
        ) from exc

    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise ApiError(
            "Bukti pembayaran tidak ditemukan.",
            status_code=404,
            code="payment_proof_file_not_found",
        )

    return candidate


def delete_payment_proof(relative_path: str) -> None:
    try:
        root = _storage_root()
        candidate = (root / relative_path).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            candidate.unlink()
    except (OSError, RuntimeError):
        # Kegagalan membersihkan file tidak boleh menggagalkan request utama.
        from flask import current_app

        current_app.logger.warning(
            "Gagal menghapus file bukti pembayaran: %s", relative_path
        )
