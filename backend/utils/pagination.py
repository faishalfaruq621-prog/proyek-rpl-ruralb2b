"""Helper pagination query string."""

from flask import request

from utils.api_error import ApiError


def get_pagination_args(
    default_per_page: int = 20,
    max_per_page: int = 100,
) -> tuple[int, int]:
    raw_page = request.args.get("page", "1")
    raw_per_page = request.args.get("per_page", str(default_per_page))

    try:
        page = int(raw_page)
        per_page = int(raw_per_page)
    except (TypeError, ValueError) as exc:
        raise ApiError(
            "Parameter page dan per_page harus berupa angka.",
            status_code=422,
            errors={
                "page": "Gunakan angka bulat minimal 1.",
                "per_page": "Gunakan angka bulat minimal 1.",
            },
        ) from exc

    if page < 1:
        raise ApiError(
            "Parameter page tidak valid.",
            status_code=422,
            errors={"page": "Minimal 1."},
        )

    if per_page < 1 or per_page > max_per_page:
        raise ApiError(
            "Parameter per_page tidak valid.",
            status_code=422,
            errors={"per_page": f"Gunakan angka 1-{max_per_page}."},
        )

    return page, per_page


def pagination_meta(pagination) -> dict:
    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }
