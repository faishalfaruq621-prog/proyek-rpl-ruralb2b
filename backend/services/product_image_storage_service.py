"""Penyimpanan gambar produk di luar direktori publik."""

from pathlib import Path
from uuid import uuid4

from flask import current_app

from utils.api_error import ApiError

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

_MIME_BY_EXTENSION = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def _storage_root() -> Path:
    root = Path(current_app.config["PRODUCT_IMAGE_UPLOAD_DIR"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _detect_image_type(head: bytes) -> str | None:
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def image_mimetype(file_path: str) -> str:
    extension = Path(file_path).suffix.lower().lstrip(".")
    return _MIME_BY_EXTENSION.get(extension, "application/octet-stream")


def safe_image_download_name(
    product_id: int, image_id: int, file_path: str
) -> str:
    suffix = Path(file_path).suffix.lower()
    return f"product_{int(product_id)}_image_{int(image_id)}{suffix}"


def save_product_image(file_storage, product_id: int) -> str:
    """Memvalidasi dan menyimpan gambar, lalu mengembalikan path relatif."""

    original_name = getattr(file_storage, "filename", "") or ""
    extension = Path(original_name).suffix.lower().lstrip(".")

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ApiError(
            "Jenis gambar tidak diizinkan.",
            status_code=422,
            errors={"file": "Gunakan gambar JPG, JPEG, PNG, atau WEBP."},
            code="invalid_image_type",
        )

    max_size = int(current_app.config["MAX_PRODUCT_IMAGE_SIZE"])

    try:
        data = file_storage.stream.read(max_size + 1)
    except OSError as exc:
        raise ApiError(
            "Gambar tidak dapat dibaca.",
            status_code=400,
            errors={"file": "Pastikan gambar tidak rusak."},
            code="image_read_error",
        ) from exc

    if not data:
        raise ApiError(
            "Gambar kosong.",
            status_code=422,
            errors={"file": "File gambar tidak boleh kosong."},
            code="empty_image",
        )

    if len(data) > max_size:
        raise ApiError(
            "Ukuran gambar terlalu besar.",
            status_code=413,
            errors={
                "file": f"Ukuran maksimal {max_size // (1024 * 1024)} MB."
            },
            code="image_too_large",
            details={"max_size_bytes": max_size},
        )

    expected_type = "jpeg" if extension in {"jpg", "jpeg"} else extension
    detected_type = _detect_image_type(data[:16])
    if detected_type != expected_type:
        raise ApiError(
            "Isi gambar tidak sesuai dengan ekstensinya.",
            status_code=422,
            errors={
                "file": "File harus benar-benar berupa JPG, JPEG, PNG, atau WEBP."
            },
            code="invalid_image_content",
        )

    root = _storage_root()
    absolute_dir = root / f"product_{int(product_id)}"

    try:
        absolute_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{uuid4().hex}.{extension}"
        absolute_path = absolute_dir / file_name
        absolute_path.write_bytes(data)
    except OSError as exc:
        raise ApiError(
            "Gambar gagal disimpan.",
            status_code=500,
            code="image_storage_error",
        ) from exc

    return absolute_path.relative_to(root).as_posix()


def resolve_product_image(relative_path: str) -> Path:
    """Mengembalikan path absolut aman atau 404 jika tidak ditemukan."""

    if not relative_path:
        raise ApiError(
            "File gambar tidak ditemukan.",
            status_code=404,
            code="image_file_not_found",
        )

    root = _storage_root()
    try:
        candidate = (root / relative_path).resolve()
    except (OSError, RuntimeError) as exc:
        raise ApiError(
            "File gambar tidak ditemukan.",
            status_code=404,
            code="image_file_not_found",
        ) from exc

    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise ApiError(
            "File gambar tidak ditemukan.",
            status_code=404,
            code="image_file_not_found",
        )

    return candidate


def delete_product_image(relative_path: str) -> None:
    try:
        root = _storage_root()
        candidate = (root / relative_path).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            candidate.unlink()
    except (OSError, RuntimeError):
        current_app.logger.warning(
            "Gagal menghapus file gambar produk: %s", relative_path
        )


def normalize_primary_flag(value) -> bool:
    if value is None or (isinstance(value, str) and not value.strip()):
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    raise ApiError(
        "Validasi gagal.",
        status_code=422,
        errors={"is_primary": "Nilai harus true atau false."},
    )
