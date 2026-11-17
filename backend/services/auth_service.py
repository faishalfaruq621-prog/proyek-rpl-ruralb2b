"""Logika bisnis autentikasi (registrasi dan login)."""

from flask import current_app
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import BusinessProfile, User
from utils.api_error import ApiError
from utils.jwt_utils import create_access_token
from utils.validators import (
    BUSINESS_TYPES,
    POSTAL_CODE_PATTERN,
    is_valid_email,
    is_valid_phone,
    normalize_email,
    normalize_text,
    password_errors,
)

# Hash palsu untuk menjaga waktu respons login saat email tidak terdaftar.
_DUMMY_PASSWORD_HASH = generate_password_hash("RuralB2B-dummy-password-2026")


def _optional_text(
    data: dict,
    field: str,
    label: str,
    max_length: int,
    errors: dict,
) -> str | None:
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        errors[field] = f"{label} harus berupa teks."
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) > max_length:
        errors[field] = f"{label} maksimal {max_length} karakter."
        return None
    return value


def _validate_registration(data: dict) -> dict:
    errors: dict[str, str] = {}

    full_name = normalize_text(data.get("full_name"))
    if not full_name:
        errors["full_name"] = "Nama lengkap wajib diisi."
    elif len(full_name) < 2:
        errors["full_name"] = "Nama lengkap minimal 2 karakter."
    elif len(full_name) > 150:
        errors["full_name"] = "Nama lengkap maksimal 150 karakter."

    email = normalize_email(data.get("email"))
    if not email:
        errors["email"] = "Email wajib diisi."
    elif not is_valid_email(email):
        errors["email"] = "Format email tidak valid."

    password = data.get("password")
    password_messages = password_errors(password)
    if password_messages:
        errors["password"] = " ".join(password_messages)

    phone = _optional_text(data, "phone", "Nomor telepon", 30, errors)
    if phone and not is_valid_phone(phone):
        errors["phone"] = (
            "Nomor telepon tidak valid. Gunakan 8-15 digit angka, "
            "boleh diawali tanda +."
        )

    raw_business_type = data.get("business_type")
    if raw_business_type is not None and not isinstance(raw_business_type, str):
        errors["business_type"] = "Jenis akun bisnis harus berupa teks."
        business_type = "other"
    elif raw_business_type is None or normalize_text(raw_business_type) == "":
        business_type = "other"
    else:
        business_type = normalize_text(raw_business_type).lower()
        if business_type not in BUSINESS_TYPES:
            errors["business_type"] = (
                "Jenis akun bisnis tidak valid. Pilihan yang tersedia: "
                + ", ".join(sorted(BUSINESS_TYPES))
                + "."
            )

    business_name = _optional_text(
        data, "business_name", "Nama bisnis", 180, errors
    ) or full_name

    address = _optional_text(data, "address", "Alamat", 2000, errors)
    village = _optional_text(data, "village", "Desa/kelurahan", 120, errors)
    district = _optional_text(data, "district", "Kecamatan", 120, errors)
    city = _optional_text(data, "city", "Kabupaten/kota", 120, errors)
    province = _optional_text(data, "province", "Provinsi", 120, errors)
    postal_code = _optional_text(
        data, "postal_code", "Kode pos", 15, errors
    )
    if postal_code and not POSTAL_CODE_PATTERN.fullmatch(postal_code):
        errors["postal_code"] = (
            "Kode pos hanya boleh berisi huruf, angka, atau tanda hubung "
            "(3-15 karakter)."
        )

    description = _optional_text(
        data, "description", "Deskripsi usaha", 2000, errors
    )

    if errors:
        raise ApiError("Validasi gagal.", 422, errors=errors)

    return {
        "full_name": full_name,
        "email": email,
        "password": password,
        "phone": phone,
        "business_type": business_type,
        "business_name": business_name,
        "address": address,
        "village": village,
        "district": district,
        "city": city,
        "province": province,
        "postal_code": postal_code,
        "description": description,
    }


def register_user(data: dict) -> User:
    """Membuat user baru beserta profil bisnisnya.

    Role selalu ``business_user``. Permintaan untuk mendaftar sebagai admin
    ditolak secara eksplisit.
    """

    requested_role = data.get("role")
    if requested_role is not None:
        if not isinstance(requested_role, str) or requested_role.strip() not in {
            "",
            "business_user",
        }:
            raise ApiError(
                "Pendaftaran sebagai admin tidak diizinkan.",
                status_code=403,
                errors={"role": "Role yang diizinkan hanya business_user."},
                code="forbidden_role",
            )

    values = _validate_registration(data)

    existing_user = db.session.scalar(
        db.select(User).where(User.email == values["email"])
    )
    if existing_user is not None:
        raise ApiError(
            "Email sudah terdaftar.",
            status_code=409,
            errors={"email": "Gunakan email lain atau masuk ke akun Anda."},
            code="email_already_registered",
        )

    user = User(
        full_name=values["full_name"],
        email=values["email"],
        role="business_user",
        account_status="active",
    )
    user.set_password(values["password"])

    profile = BusinessProfile(
        user=user,
        business_name=values["business_name"],
        business_type=values["business_type"],
        phone=values["phone"],
        address=values["address"],
        village=values["village"],
        district=values["district"],
        city=values["city"],
        province=values["province"],
        postal_code=values["postal_code"],
        description=values["description"],
    )

    db.session.add(user)
    db.session.add(profile)

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        error_code = None
        if getattr(exc, "orig", None) is not None and exc.orig.args:
            error_code = exc.orig.args[0]
        if error_code == 1062:
            raise ApiError(
                "Email sudah terdaftar.",
                status_code=409,
                errors={"email": "Gunakan email lain atau masuk ke akun Anda."},
                code="email_already_registered",
            ) from exc
        current_app.logger.error(
            "Gagal menyimpan pengguna baru: %s", getattr(exc, "orig", exc)
        )
        raise ApiError(
            "Registrasi gagal karena kesalahan pada server.",
            status_code=500,
        ) from exc

    db.session.refresh(user)
    return user


def login_user(data: dict) -> dict:
    """Memverifikasi kredensial dan mengembalikan access token."""

    errors: dict[str, str] = {}

    email = normalize_email(data.get("email"))
    if not email:
        errors["email"] = "Email wajib diisi."
    elif not is_valid_email(email):
        errors["email"] = "Format email tidak valid."

    password = data.get("password")
    if not isinstance(password, str) or not password:
        errors["password"] = "Password wajib diisi."

    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)

    user = db.session.scalar(db.select(User).where(User.email == email))

    if user is None:
        # Tetap lakukan verifikasi hash agar waktu respons tidak membocorkan
        # apakah email terdaftar atau tidak.
        check_password_hash(_DUMMY_PASSWORD_HASH, password)
        raise ApiError(
            "Email atau password salah.",
            status_code=401,
            code="invalid_credentials",
        )

    if not user.check_password(password):
        raise ApiError(
            "Email atau password salah.",
            status_code=401,
            code="invalid_credentials",
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

    token, expires_at, _ = create_access_token(user)

    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": current_app.config["JWT_EXPIRES_MINUTES"] * 60,
        "expires_at": expires_at.isoformat(),
        "user": user.to_dict(),
    }

def validate_change_password_payload(data: dict) -> dict:
    """Validasi payload perubahan password akun yang sedang login."""
    if not isinstance(data, dict):
        raise ApiError(
            "Body request harus berupa objek JSON yang valid.",
            status_code=400,
            code="invalid_json",
        )

    errors: dict[str, str] = {}
    current_password = data.get("current_password")
    if not isinstance(current_password, str) or not current_password:
        errors["current_password"] = "Password saat ini wajib diisi."

    new_password = data.get("new_password")
    if not isinstance(new_password, str) or not new_password:
        errors["new_password"] = "Password baru wajib diisi."
    else:
        pw_issues = password_errors(new_password)
        if pw_issues:
            errors["new_password"] = pw_issues

    if errors:
        raise ApiError(
            "Validasi gagal.", status_code=422, errors=errors
        )
    return {"current_password": current_password, "new_password": new_password}
