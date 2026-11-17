"""Validasi payload keranjang, pesanan, status, dan pembayaran."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from utils.api_error import ApiError

ORDER_STATUSES = {
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "completed",
    "cancelled",
}

SELLER_STATUS_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["processing", "cancelled"],
    "processing": ["shipped", "cancelled"],
    "shipped": ["completed"],
    "completed": [],
    "cancelled": [],
}

BUYER_CANCELLABLE_STATUSES = {"pending"}

# Status pesanan yang masih menerima pengajuan info pembayaran dari pembeli.
# Status pemenuhan (processing/shipped) dan status terminal (completed atau
# cancelled) tidak boleh menerima pengajuan pembayaran baru.
BUYER_PAYMENT_SUBMITTABLE_STATUSES = {"pending", "confirmed"}

MAX_UNSIGNED_INT = 4_294_967_295
MAX_ORDER_TOTAL = Decimal("999999999999.99")
MAX_SHIPPING_ADDRESS_LENGTH = 2000
MAX_NOTE_LENGTH = 2000
MAX_PAYMENT_METHOD_LENGTH = 80
MAX_PAYMENT_REFERENCE_LENGTH = 150
MAX_SEARCH_LENGTH = 180
ORDER_SORT_OPTIONS = {"newest", "oldest"}


def ensure_not_self_purchase(
    *,
    buyer=None,
    seller_profile_id=None,
    buyer_user_id=None,
    seller_user_id=None,
    message: str = "Pembelian dari profil bisnis sendiri tidak diizinkan.",
) -> None:
    """Tolak transaksi yang melibatkan bisnis/pengguna yang sama.

    Dipakai pada keranjang, checkout, dan konfirmasi pembayaran agar pembeli
    tidak dapat membeli dari profil bisnisnya sendiri, dan penjual tidak
    dapat mengonfirmasi pembayaran untuk pesanan yang ia beli sendiri.
    """

    buyer_profile = getattr(buyer, "business_profile", None)
    buyer_profile_id = getattr(buyer_profile, "id", None)
    same_profile = (
        buyer_profile_id is not None
        and seller_profile_id is not None
        and buyer_profile_id == seller_profile_id
    )
    same_user = (
        buyer_user_id is not None
        and seller_user_id is not None
        and buyer_user_id == seller_user_id
    )
    if same_profile or same_user:
        raise ApiError(
            message,
            status_code=409,
            code="self_purchase_not_allowed",
        )


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
    errors: dict,
) -> str | None:
    if not isinstance(value, str):
        errors[field] = f"{label} wajib diisi dan harus berupa teks."
        return None
    value = value.strip()
    if not value:
        errors[field] = f"{label} wajib diisi."
        return None
    if len(value) > max_length:
        errors[field] = f"{label} maksimal {max_length} karakter."
        return None
    return value


def _integer(
    value,
    field: str,
    label: str,
    minimum: int,
    maximum: int,
    errors: dict,
) -> int | None:
    if isinstance(value, bool):
        errors[field] = f"{label} harus berupa angka bulat."
        return None

    if isinstance(value, int):
        number = value
    elif isinstance(value, str):
        try:
            number = int(value.strip())
        except (TypeError, ValueError):
            errors[field] = f"{label} harus berupa angka bulat."
            return None
    else:
        errors[field] = f"{label} harus berupa angka bulat."
        return None

    if number < minimum or number > maximum:
        errors[field] = (
            f"{label} harus berada di antara {minimum} dan {maximum}."
        )
        return None
    return number


def _parse_datetime(value, field: str, label: str, errors: dict):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if not isinstance(value, str):
        errors[field] = f"{label} harus berupa tanggal ISO 8601."
        return None

    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        errors[field] = (
            f"{label} tidak valid. Gunakan format ISO 8601, "
            "misalnya 2026-11-08T14:30:00."
        )
        return None

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)

    if parsed > datetime.now():
        errors[field] = f"{label} tidak boleh berada di masa depan."
        return None

    return parsed


def validate_cart_item_create_payload(data: dict) -> dict:
    errors: dict[str, str] = {}
    allowed = {"product_id", "quantity"}
    unknown = sorted(set(data.keys()) - allowed)
    if unknown:
        errors["_request"] = (
            "Field tidak dikenal: " + ", ".join(unknown) + "."
        )

    values: dict = {}

    if "product_id" not in data:
        errors["product_id"] = "Produk wajib dipilih."
    else:
        product_id = _integer(
            data.get("product_id"),
            "product_id",
            "Produk",
            1,
            MAX_UNSIGNED_INT,
            errors,
        )
        if product_id is not None:
            values["product_id"] = product_id

    if "quantity" not in data:
        values["quantity"] = 1
    else:
        quantity = _integer(
            data.get("quantity"),
            "quantity",
            "Jumlah",
            1,
            MAX_UNSIGNED_INT,
            errors,
        )
        if quantity is not None:
            values["quantity"] = quantity

    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)
    return values


def validate_cart_item_update_payload(data: dict) -> dict:
    errors: dict[str, str] = {}
    allowed = {"quantity"}
    unknown = sorted(set(data.keys()) - allowed)
    if unknown:
        errors["_request"] = (
            "Field tidak dikenal: " + ", ".join(unknown) + "."
        )

    if "quantity" not in data:
        errors["quantity"] = "Jumlah wajib diisi."
        quantity = None
    else:
        quantity = _integer(
            data.get("quantity"),
            "quantity",
            "Jumlah",
            1,
            MAX_UNSIGNED_INT,
            errors,
        )

    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)
    return {"quantity": quantity}


def validate_checkout_payload(data: dict) -> dict:
    errors: dict[str, str] = {}
    allowed = {
        "shipping_address",
        "buyer_note",
        "payment_method",
        "payment_reference",
    }
    unknown = sorted(set(data.keys()) - allowed)
    if unknown:
        errors["_request"] = (
            "Field tidak dikenal: " + ", ".join(unknown) + "."
        )

    values = {
        "shipping_address": _optional_text(
            data.get("shipping_address"),
            "shipping_address",
            "Alamat pengiriman",
            MAX_SHIPPING_ADDRESS_LENGTH,
            errors,
        ),
        "buyer_note": _optional_text(
            data.get("buyer_note"),
            "buyer_note",
            "Catatan pembeli",
            MAX_NOTE_LENGTH,
            errors,
        ),
        "payment_method": _optional_text(
            data.get("payment_method"),
            "payment_method",
            "Metode pembayaran",
            MAX_PAYMENT_METHOD_LENGTH,
            errors,
        ),
        "payment_reference": _optional_text(
            data.get("payment_reference"),
            "payment_reference",
            "Referensi pembayaran",
            MAX_PAYMENT_REFERENCE_LENGTH,
            errors,
        ),
    }

    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)
    return values


def validate_cancel_payload(data: dict) -> dict:
    errors: dict[str, str] = {}
    allowed = {"reason", "notes"}
    unknown = sorted(set(data.keys()) - allowed)
    if unknown:
        errors["_request"] = (
            "Field tidak dikenal: " + ", ".join(unknown) + "."
        )

    values = {
        "reason": _optional_text(
            data.get("reason"),
            "reason",
            "Alasan pembatalan",
            MAX_NOTE_LENGTH,
            errors,
        ),
        "notes": _optional_text(
            data.get("notes"),
            "notes",
            "Catatan pembatalan",
            MAX_NOTE_LENGTH,
            errors,
        ),
    }

    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)
    return values


def validate_order_status_payload(data: dict) -> dict:
    errors: dict[str, str] = {}
    allowed = {"status", "notes"}
    unknown = sorted(set(data.keys()) - allowed)
    if unknown:
        errors["_request"] = (
            "Field tidak dikenal: " + ", ".join(unknown) + "."
        )

    status = None
    if "status" not in data:
        errors["status"] = "Status pesanan wajib diisi."
    elif not isinstance(data.get("status"), str):
        errors["status"] = "Status pesanan harus berupa teks."
    else:
        status = data["status"].strip().lower()
        if status not in ORDER_STATUSES:
            errors["status"] = (
                "Status pesanan tidak valid. Pilihan: "
                + ", ".join(sorted(ORDER_STATUSES))
                + "."
            )
            status = None

    notes = _optional_text(
        data.get("notes"),
        "notes",
        "Catatan status",
        MAX_NOTE_LENGTH,
        errors,
    )

    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)
    return {"status": status, "notes": notes}


def validate_payment_submit_payload(data: dict) -> dict:
    errors: dict[str, str] = {}
    allowed = {"payment_method", "payment_reference", "paid_at"}
    unknown = sorted(set(data.keys()) - allowed)
    if unknown:
        errors["_request"] = (
            "Field tidak dikenal: " + ", ".join(unknown) + "."
        )

    if not set(data.keys()) & allowed:
        errors["_request"] = "Tidak ada informasi pembayaran yang dikirim."

    values: dict = {}

    if "payment_method" in data:
        method = _required_text(
            data.get("payment_method"),
            "payment_method",
            "Metode pembayaran",
            MAX_PAYMENT_METHOD_LENGTH,
            errors,
        )
        if method is not None:
            values["payment_method"] = method

    if "payment_reference" in data:
        values["payment_reference"] = _optional_text(
            data.get("payment_reference"),
            "payment_reference",
            "Referensi pembayaran",
            MAX_PAYMENT_REFERENCE_LENGTH,
            errors,
        )

    if "paid_at" in data:
        paid_at = _parse_datetime(
            data.get("paid_at"), "paid_at", "Tanggal pembayaran", errors
        )
        if paid_at is not None:
            values["paid_at"] = paid_at

    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)
    return values


def validate_payment_confirm_payload(data: dict) -> dict:
    errors: dict[str, str] = {}
    allowed = {"payment_method", "payment_reference", "paid_at"}
    unknown = sorted(set(data.keys()) - allowed)
    if unknown:
        errors["_request"] = (
            "Field tidak dikenal: " + ", ".join(unknown) + "."
        )

    values: dict = {}

    if "payment_method" in data:
        method = _required_text(
            data.get("payment_method"),
            "payment_method",
            "Metode pembayaran",
            MAX_PAYMENT_METHOD_LENGTH,
            errors,
        )
        if method is not None:
            values["payment_method"] = method

    if "payment_reference" in data:
        values["payment_reference"] = _optional_text(
            data.get("payment_reference"),
            "payment_reference",
            "Referensi pembayaran",
            MAX_PAYMENT_REFERENCE_LENGTH,
            errors,
        )

    if "paid_at" in data:
        paid_at = _parse_datetime(
            data.get("paid_at"), "paid_at", "Tanggal pembayaran", errors
        )
        if paid_at is not None:
            values["paid_at"] = paid_at

    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)
    return values


def validate_order_filter_status(value) -> str | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if not isinstance(value, str):
        raise ApiError(
            "Filter status tidak valid.",
            status_code=422,
            errors={"status": "Filter status harus berupa teks."},
        )
    status = value.strip().lower()
    if status not in ORDER_STATUSES:
        raise ApiError(
            "Filter status tidak valid.",
            status_code=422,
            errors={
                "status": "Pilihan: "
                + ", ".join(sorted(ORDER_STATUSES))
                + "."
            },
        )
    return status


def validate_order_sort(value) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        return "newest"
    if not isinstance(value, str):
        raise ApiError(
            "Parameter sort tidak valid.",
            status_code=422,
            errors={"sort": "Gunakan newest atau oldest."},
        )
    sort = value.strip().lower()
    if sort not in ORDER_SORT_OPTIONS:
        raise ApiError(
            "Parameter sort tidak valid.",
            status_code=422,
            errors={"sort": "Gunakan newest atau oldest."},
        )
    return sort


def validate_order_search(value) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={"q": "Pencarian harus berupa teks."},
        )
    value = value.strip()
    if not value:
        return None
    if len(value) > MAX_SEARCH_LENGTH:
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={"q": f"Pencarian maksimal {MAX_SEARCH_LENGTH} karakter."},
        )
    return value


def validate_order_total(value: Decimal) -> Decimal:
    try:
        total = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ApiError(
            "Total pesanan tidak valid.",
            status_code=422,
            code="invalid_order_total",
        ) from exc

    if total < 0:
        raise ApiError(
            "Total pesanan tidak boleh negatif.",
            status_code=422,
            code="invalid_order_total",
        )
    if total > MAX_ORDER_TOTAL:
        raise ApiError(
            "Total pesanan melebihi batas maksimum.",
            status_code=422,
            code="order_total_too_large",
            details={"max_total": float(MAX_ORDER_TOTAL)},
        )
    return total
