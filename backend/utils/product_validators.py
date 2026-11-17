"""Validasi payload produk, inventori, dan filter katalog."""

from decimal import Decimal, InvalidOperation

from utils.api_error import ApiError

PRODUCT_STATUSES = {"active", "inactive", "out_of_stock"}
PRODUCT_FIELDS = {
    "product_name",
    "description",
    "category_id",
    "price",
    "unit",
    "minimum_order",
    "product_status",
}
MAX_UNSIGNED_INT = 4_294_967_295
MAX_PRICE = Decimal("999999999999.99")
MAX_DESCRIPTION_LENGTH = 5000
SORT_OPTIONS = {
    "newest",
    "oldest",
    "price_asc",
    "price_desc",
    "name_asc",
    "name_desc",
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
    min_length: int,
    max_length: int,
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
        errors[field] = f"{label} harus berada di antara {minimum} dan {maximum}."
        return None

    return number


def _price(value, field: str, label: str, errors: dict) -> Decimal | None:
    if isinstance(value, bool):
        errors[field] = f"{label} harus berupa angka."
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            errors[field] = f"{label} wajib diisi."
            return None

    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        errors[field] = f"{label} harus berupa angka yang valid."
        return None

    if not number.is_finite():
        errors[field] = f"{label} harus berupa angka yang valid."
        return None

    if number < 0 or number > MAX_PRICE:
        errors[field] = f"{label} harus berada di antara 0 dan {MAX_PRICE}."
        return None

    try:
        rounded = number.quantize(Decimal("0.01"))
    except InvalidOperation:
        errors[field] = f"{label} memiliki format angka yang tidak valid."
        return None

    if rounded != number:
        errors[field] = f"{label} maksimal 2 angka desimal."
        return None

    return rounded


def _parse_bool(value, field: str, label: str, errors: dict) -> bool | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    errors[field] = f"{label} harus bernilai true atau false."
    return None


def validate_product_payload(
    data: dict,
    partial: bool = False,
    allow_stock: bool = False,
) -> dict:
    """Memvalidasi payload create/update produk.

    ``allow_stock=True`` hanya dipakai saat create untuk stok awal.
    Perubahan stok setelah itu dilakukan lewat endpoint inventori.
    """

    errors: dict[str, str] = {}
    allowed_fields = set(PRODUCT_FIELDS)
    if allow_stock:
        allowed_fields.add("stock_quantity")

    unknown_fields = sorted(set(data.keys()) - allowed_fields)
    if unknown_fields:
        errors["_request"] = (
            "Field tidak dikenal: " + ", ".join(unknown_fields) + "."
        )

    if (
        partial
        and not (set(data.keys()) & allowed_fields)
        and not unknown_fields
    ):
        errors["_request"] = "Tidak ada field produk yang diubah."

    values: dict = {}

    if not partial or "product_name" in data:
        if not partial and "product_name" not in data:
            errors["product_name"] = "Nama produk wajib diisi."
        else:
            product_name = _required_text(
                data.get("product_name"),
                "product_name",
                "Nama produk",
                2,
                180,
                errors,
            )
            if product_name is not None:
                values["product_name"] = product_name

    if not partial or "description" in data:
        values["description"] = _optional_text(
            data.get("description"),
            "description",
            "Deskripsi produk",
            MAX_DESCRIPTION_LENGTH,
            errors,
        )

    if not partial or "category_id" in data:
        raw_category = data.get("category_id")
        if raw_category is None or (
            isinstance(raw_category, str) and not raw_category.strip()
        ):
            values["category_id"] = None
        else:
            category_id = _integer(
                raw_category,
                "category_id",
                "Kategori",
                1,
                MAX_UNSIGNED_INT,
                errors,
            )
            if category_id is not None:
                values["category_id"] = category_id

    if not partial or "price" in data:
        if not partial and "price" not in data:
            errors["price"] = "Harga wajib diisi."
        else:
            price = _price(data.get("price"), "price", "Harga", errors)
            if price is not None:
                values["price"] = price

    if not partial or "unit" in data:
        if not partial and "unit" not in data:
            errors["unit"] = "Satuan produk wajib diisi."
        else:
            unit = _required_text(
                data.get("unit"),
                "unit",
                "Satuan produk",
                1,
                40,
                errors,
            )
            if unit is not None:
                values["unit"] = unit

    if not partial or "minimum_order" in data:
        if "minimum_order" in data:
            minimum_order = _integer(
                data.get("minimum_order"),
                "minimum_order",
                "Minimum order",
                1,
                MAX_UNSIGNED_INT,
                errors,
            )
            if minimum_order is not None:
                values["minimum_order"] = minimum_order
        elif not partial:
            values["minimum_order"] = 1

    if not partial or "product_status" in data:
        if "product_status" in data:
            raw_status = data.get("product_status")
            if not isinstance(raw_status, str):
                errors["product_status"] = "Status produk harus berupa teks."
            else:
                product_status = raw_status.strip().lower()
                if product_status not in PRODUCT_STATUSES:
                    errors["product_status"] = (
                        "Status produk tidak valid. Pilihan: "
                        + ", ".join(sorted(PRODUCT_STATUSES))
                        + "."
                    )
                else:
                    values["product_status"] = product_status
        elif not partial:
            values["product_status"] = "active"

    if allow_stock and (not partial or "stock_quantity" in data):
        if "stock_quantity" in data:
            stock_quantity = _integer(
                data.get("stock_quantity"),
                "stock_quantity",
                "Stok awal",
                0,
                MAX_UNSIGNED_INT,
                errors,
            )
            if stock_quantity is not None:
                values["stock_quantity"] = stock_quantity
        elif not partial:
            values["stock_quantity"] = 0

    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)

    return values


def validate_inventory_payload(data: dict) -> dict:
    """Memvalidasi perubahan stok: set absolut atau adjustment delta."""

    errors: dict[str, str] = {}
    unknown_fields = sorted(set(data.keys()) - {"stock_quantity", "adjustment"})
    if unknown_fields:
        errors["_request"] = (
            "Field tidak dikenal: " + ", ".join(unknown_fields) + "."
        )

    has_stock = "stock_quantity" in data
    has_adjustment = "adjustment" in data

    if has_stock == has_adjustment:
        errors["_request"] = (
            "Kirim salah satu: stock_quantity (set absolut) atau "
            "adjustment (tambah/kurangi)."
        )

    values: dict = {}

    if has_stock:
        stock_quantity = _integer(
            data.get("stock_quantity"),
            "stock_quantity",
            "Stok",
            0,
            MAX_UNSIGNED_INT,
            errors,
        )
        if stock_quantity is not None:
            values["stock_quantity"] = stock_quantity

    if has_adjustment:
        adjustment = _integer(
            data.get("adjustment"),
            "adjustment",
            "Perubahan stok",
            -MAX_UNSIGNED_INT,
            MAX_UNSIGNED_INT,
            errors,
        )
        if adjustment is not None:
            values["adjustment"] = adjustment

    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)

    return values


def validate_positive_int_filter(
    value, field: str, label: str, allow_none: bool = True
) -> int | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        if allow_none:
            return None
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={field: f"{label} wajib diisi."},
        )

    errors: dict[str, str] = {}
    number = _integer(value, field, label, 1, MAX_UNSIGNED_INT, errors)
    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)
    return number


def validate_price_filter(value, field: str, label: str) -> Decimal | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None

    errors: dict[str, str] = {}
    number = _price(value, field, label, errors)
    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)
    return number


def validate_bool_filter(value, field: str, label: str) -> bool | None:
    errors: dict[str, str] = {}
    result = _parse_bool(value, field, label, errors)
    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)
    return result


def validate_text_filter(
    value, field: str, label: str, max_length: int
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={field: f"{label} harus berupa teks."},
        )
    value = value.strip()
    if not value:
        return None
    if len(value) > max_length:
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={field: f"{label} maksimal {max_length} karakter."},
        )
    return value


def validate_sort(value) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        return "newest"
    if not isinstance(value, str) or value.strip().lower() not in SORT_OPTIONS:
        raise ApiError(
            "Parameter sort tidak valid.",
            status_code=422,
            errors={
                "sort": "Pilihan: " + ", ".join(sorted(SORT_OPTIONS)) + "."
            },
        )
    return value.strip().lower()
