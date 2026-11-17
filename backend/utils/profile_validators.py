"""Validasi payload profil bisnis."""

from decimal import Decimal, InvalidOperation

from utils.api_error import ApiError
from utils.validators import (
    BUSINESS_TYPES,
    POSTAL_CODE_PATTERN,
    is_valid_phone,
)

PROFILE_FIELDS = {
    "business_name",
    "business_type",
    "phone",
    "address",
    "village",
    "district",
    "city",
    "province",
    "postal_code",
    "latitude",
    "longitude",
    "description",
    "can_buy",
    "can_sell",
}

_CAPABILITY_FIELDS = ("can_buy", "can_sell")

_SHORT_TEXT_FIELDS = {
    "village": ("Desa/kelurahan", 120),
    "district": ("Kecamatan", 120),
    "city": ("Kabupaten/kota", 120),
    "province": ("Provinsi", 120),
}


def _optional_text(
    value,
    field: str,
    label: str,
    max_length: int,
    errors: dict,
) -> str | None:
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


def _required_text(
    value,
    field: str,
    label: str,
    max_length: int,
    min_length: int,
    errors: dict,
) -> str | None:
    if not isinstance(value, str):
        errors[field] = f"{label} wajib diisi dan harus berupa teks."
        return None
    value = value.strip()
    if not value:
        errors[field] = f"{label} wajib diisi."
    elif len(value) < min_length:
        errors[field] = f"{label} minimal {min_length} karakter."
    elif len(value) > max_length:
        errors[field] = f"{label} maksimal {max_length} karakter."
    else:
        return value
    return None


def _optional_decimal(
    value,
    field: str,
    label: str,
    minimum: Decimal,
    maximum: Decimal,
    errors: dict,
) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool):
        errors[field] = f"{label} harus berupa angka."
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        errors[field] = f"{label} harus berupa angka yang valid."
        return None

    if not number.is_finite():
        errors[field] = f"{label} harus berupa angka yang valid."
        return None

    if number < minimum or number > maximum:
        errors[field] = (
            f"{label} harus berada di antara {minimum} dan {maximum}."
        )
        return None

    try:
        return number.quantize(Decimal("0.0000001"))
    except InvalidOperation:
        errors[field] = f"{label} memiliki format angka yang tidak valid."
        return None


def validate_business_profile_payload(data: dict, partial: bool = False) -> dict:
    """Memvalidasi dan mengembalikan nilai yang siap disimpan.

    ``partial=True`` dipakai untuk PATCH: field yang tidak dikirim tidak
    diubah. ``partial=False`` dipakai untuk PUT: field opsional yang tidak
    dikirim akan dikosongkan.
    """

    errors: dict[str, str] = {}

    unknown_fields = sorted(set(data.keys()) - PROFILE_FIELDS)
    if unknown_fields:
        errors["_request"] = (
            "Field tidak dikenal: " + ", ".join(unknown_fields) + "."
        )

    if partial and not (set(data.keys()) & PROFILE_FIELDS):
        errors["_request"] = "Tidak ada field profil yang diubah."

    values: dict = {}

    # Kemampuan akun (boolean). Pengguna lama dengan nilai NULL setelah
    # migration tetap dianggap berlaku default (1); di sini hanya menerima
    # boolean eksplisit.
    for cap_field in _CAPABILITY_FIELDS:
        if not partial or cap_field in data:
            raw = data.get(cap_field)
            if raw is None:
                continue
            if isinstance(raw, bool):
                values[cap_field] = bool(raw)
            elif isinstance(raw, int) and raw in (0, 1):
                values[cap_field] = bool(raw)
            elif isinstance(raw, str) and raw.strip().lower() in ("true", "1"):
                values[cap_field] = True
            elif isinstance(raw, str) and raw.strip().lower() in ("false", "0"):
                values[cap_field] = False
            else:
                errors[cap_field] = (
                    "Nilai kemampuan harus true atau false."
                )

    if (values.get("can_buy") is False) and (values.get("can_sell") is False):
        errors["can_buy"] = (
            "Salah satu kemampuan (beli atau jual) harus tetap aktif."
        )

    if not partial or "business_name" in data:
        if not partial and "business_name" not in data:
            errors["business_name"] = "Nama bisnis wajib diisi."
        else:
            business_name = _required_text(
                data.get("business_name"),
                "business_name",
                "Nama bisnis",
                180,
                2,
                errors,
            )
            if business_name is not None:
                values["business_name"] = business_name

    if not partial or "business_type" in data:
        if not partial and "business_type" not in data:
            errors["business_type"] = "Jenis akun bisnis wajib diisi."
        else:
            raw_type = data.get("business_type")
            if not isinstance(raw_type, str):
                errors["business_type"] = "Jenis akun bisnis harus berupa teks."
            else:
                business_type = raw_type.strip().lower()
                if business_type not in BUSINESS_TYPES:
                    errors["business_type"] = (
                        "Jenis akun bisnis tidak valid. Pilihan yang tersedia: "
                        + ", ".join(sorted(BUSINESS_TYPES))
                        + "."
                    )
                else:
                    values["business_type"] = business_type

    if not partial or "phone" in data:
        phone = _optional_text(
            data.get("phone"), "phone", "Nomor telepon", 30, errors
        )
        if phone and not is_valid_phone(phone):
            errors["phone"] = (
                "Nomor telepon tidak valid. Gunakan 8-15 digit angka, "
                "boleh diawali tanda +."
            )
        else:
            values["phone"] = phone

    if not partial or "address" in data:
        values["address"] = _optional_text(
            data.get("address"), "address", "Alamat", 2000, errors
        )

    for field, (label, max_length) in _SHORT_TEXT_FIELDS.items():
        if not partial or field in data:
            values[field] = _optional_text(
                data.get(field), field, label, max_length, errors
            )

    if not partial or "postal_code" in data:
        postal_code = _optional_text(
            data.get("postal_code"), "postal_code", "Kode pos", 15, errors
        )
        if postal_code and not POSTAL_CODE_PATTERN.fullmatch(postal_code):
            errors["postal_code"] = (
                "Kode pos hanya boleh berisi huruf, angka, atau tanda hubung "
                "(3-15 karakter)."
            )
        else:
            values["postal_code"] = postal_code

    if not partial or "latitude" in data:
        values["latitude"] = _optional_decimal(
            data.get("latitude"),
            "latitude",
            "Latitude",
            Decimal("-90"),
            Decimal("90"),
            errors,
        )

    if not partial or "longitude" in data:
        values["longitude"] = _optional_decimal(
            data.get("longitude"),
            "longitude",
            "Longitude",
            Decimal("-180"),
            Decimal("180"),
            errors,
        )

    if not partial or "description" in data:
        values["description"] = _optional_text(
            data.get("description"), "description", "Deskripsi usaha", 2000, errors
        )

    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)

    return values
