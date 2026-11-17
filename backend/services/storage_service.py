"""Penyimpanan dokumen verifikasi di luar direktori publik."""

from pathlib import Path
from uuid import uuid4

from flask import current_app

from utils.api_error import ApiError
from utils.validators import ALLOWED_DOCUMENT_EXTENSIONS

import re

_MIME_BY_EXTENSION = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def _storage_root() -> Path:
    root = Path(current_app.config["VERIFICATION_UPLOAD_DIR"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _detect_file_type(head: bytes) -> str | None:
    if head.startswith(b"%PDF-"):
        return "pdf"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def safe_download_name(document_type: str, document_id: int, file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    safe_type = re.sub(r"[^A-Za-z0-9_-]+", "_", document_type).strip("_") or "document"
    return f"{safe_type}_{document_id}{suffix}"


def mimetype_for_path(file_path: str) -> str:
    extension = Path(file_path).suffix.lower().lstrip(".")
    return _MIME_BY_EXTENSION.get(extension, "application/octet-stream")


def save_document(file_storage, profile_id: int, verification_id: int) -> str:
    """Memvalidasi dan menyimpan file, lalu mengembalikan path relatif.

    Nama file asli tidak dipakai. File disimpan dengan UUID dan ekstensi yang
    sudah lolos validasi. Isi file diperiksa dengan magic bytes.
    """

    original_name = getattr(file_storage, "filename", "") or ""
    extension = Path(original_name).suffix.lower().lstrip(".")

    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ApiError(
            "Jenis file tidak diizinkan.",
            status_code=422,
            errors={
                "file": "Gunakan file PDF, JPG, JPEG, PNG, atau WEBP."
            },
            code="invalid_file_type",
        )

    max_size = int(current_app.config["MAX_VERIFICATION_DOCUMENT_SIZE"])

    try:
        data = file_storage.stream.read(max_size + 1)
    except OSError as exc:
        raise ApiError(
            "File tidak dapat dibaca.",
            status_code=400,
            errors={"file": "Pastikan file tidak rusak."},
            code="file_read_error",
        ) from exc

    if not data:
        raise ApiError(
            "File kosong.",
            status_code=422,
            errors={"file": "File yang diunggah tidak boleh kosong."},
            code="empty_file",
        )

    if len(data) > max_size:
        raise ApiError(
            "Ukuran file terlalu besar.",
            status_code=413,
            errors={
                "file": f"Ukuran maksimal {max_size // (1024 * 1024)} MB."
            },
            code="file_too_large",
            details={"max_size_bytes": max_size},
        )

    expected_type = "jpeg" if extension in {"jpg", "jpeg"} else extension
    detected_type = _detect_file_type(data[:16])

    if detected_type != expected_type:
        raise ApiError(
            "Isi file tidak sesuai dengan ekstensinya.",
            status_code=422,
            errors={
                "file": "File harus benar-benar berupa PDF, JPG, JPEG, PNG, atau WEBP."
            },
            code="invalid_file_content",
        )

    root = _storage_root()
    relative_dir = Path(
        f"business_{int(profile_id)}", f"verification_{int(verification_id)}"
    )
    absolute_dir = root / relative_dir

    try:
        absolute_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{uuid4().hex}.{extension}"
        absolute_path = absolute_dir / file_name
        absolute_path.write_bytes(data)
    except OSError as exc:
        raise ApiError(
            "Dokumen gagal disimpan.",
            status_code=500,
            code="storage_error",
        ) from exc

    return absolute_path.relative_to(root).as_posix()


def resolve_stored_file(relative_path: str) -> Path:
    """Mengembalikan path absolut yang aman, atau 404 jika tidak ditemukan."""

    if not relative_path:
        raise ApiError(
            "File dokumen tidak ditemukan.",
            status_code=404,
            code="document_file_not_found",
        )

    root = _storage_root()
    try:
        candidate = (root / relative_path).resolve()
    except (OSError, RuntimeError) as exc:
        raise ApiError(
            "File dokumen tidak ditemukan.",
            status_code=404,
            code="document_file_not_found",
        ) from exc

    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise ApiError(
            "File dokumen tidak ditemukan.",
            status_code=404,
            code="document_file_not_found",
        )

    return candidate


def delete_stored_file(relative_path: str) -> None:
    try:
        root = _storage_root()
        candidate = (root / relative_path).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            candidate.unlink()
    except (OSError, RuntimeError):
        # Kegagalan membersihkan file tidak boleh menggagalkan request utama.
        current_app.logger.warning(
            "Gagal menghapus file sementara dokumen verifikasi"
        )
