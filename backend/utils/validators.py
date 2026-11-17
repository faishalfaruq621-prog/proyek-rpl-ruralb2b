"""Validasi input autentikasi.

Validator dibuat eksplisit agar pesan error mudah dipahami pengguna dan
konsisten dengan batas kolom yang ada di database.
"""

import re

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)
PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9\s().-]{5,29}$")
POSTAL_CODE_PATTERN = re.compile(r"^[A-Za-z0-9-]{3,15}$")

BUSINESS_TYPES = {
    "farmer",
    "supplier",
    "collector",
    "producer",
    "shop",
    "warung",
    "other",
}

DOCUMENT_TYPES = {
    "ktp",
    "kk",
    "npwp",
    "nib",
    "siup",
    "business_photo",
    "other",
}

ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "webp"}

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def normalize_email(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        return ""
    return value.strip()


def is_valid_email(email: str) -> bool:
    if not email or len(email) > 190:
        return False
    if not EMAIL_PATTERN.fullmatch(email):
        return False

    local_part, separator, domain = email.partition("@")
    if separator != "@" or not local_part or not domain:
        return False
    if local_part.startswith(".") or local_part.endswith("."):
        return False
    if ".." in local_part or ".." in domain:
        return False

    return True


def is_valid_phone(phone: str) -> bool:
    if not phone:
        return True
    if not PHONE_PATTERN.fullmatch(phone):
        return False
    digit_count = sum(character.isdigit() for character in phone)
    return 8 <= digit_count <= 15


def password_errors(password: object) -> list[str]:
    """Mengembalikan daftar pelanggaran aturan password."""

    if not isinstance(password, str) or not password:
        return ["Password wajib diisi."]

    messages: list[str] = []
    if len(password) < PASSWORD_MIN_LENGTH:
        messages.append(f"Password minimal {PASSWORD_MIN_LENGTH} karakter.")
    if len(password) > PASSWORD_MAX_LENGTH:
        messages.append(f"Password maksimal {PASSWORD_MAX_LENGTH} karakter.")
    if not re.search(r"[a-z]", password):
        messages.append("Password harus mengandung huruf kecil.")
    if not re.search(r"[A-Z]", password):
        messages.append("Password harus mengandung huruf besar.")
    if not re.search(r"[0-9]", password):
        messages.append("Password harus mengandung angka.")
    if not re.search(r"[^A-Za-z0-9]", password):
        messages.append("Password harus mengandung karakter khusus.")
    return messages
