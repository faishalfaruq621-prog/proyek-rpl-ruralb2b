"""Helper pembacaan body JSON."""

from flask import request

from utils.api_error import ApiError


def get_json_body(required: bool = True) -> dict:
    if not request.is_json:
        if not required and not request.data:
            return {}
        raise ApiError(
            "Content-Type harus application/json.",
            status_code=415,
            code="unsupported_media_type",
        )

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(
            "Body request harus berupa objek JSON yang valid.",
            status_code=400,
            code="invalid_json",
        )

    return data


def get_optional_json_body() -> dict:
    """Membaca body JSON opsional; body kosong dianggap ``{}``."""

    if not request.data:
        return {}
    return get_json_body(required=False)
