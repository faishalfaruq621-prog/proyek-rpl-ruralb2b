"""Service panel admin: statistik aktual, pengguna, kategori, transaksi."""

from sqlalchemy import func, or_, select

from extensions import db
from models import (
    BusinessProfile,
    Category,
    Order,
    OrderItem,
    Product,
    User,
)
from services.notification_service import create_notification
from utils.api_error import ApiError

_ORDER_STATUSES = (
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "completed",
    "cancelled",
)


def admin_stats() -> dict:
    users_total = db.session.scalar(select(func.count()).select_from(User)) or 0
    users_active = db.session.scalar(
        select(func.count()).select_from(User).where(
            User.account_status == "active"
        )
    ) or 0
    profiles_total = db.session.scalar(
        select(func.count()).select_from(BusinessProfile)
    ) or 0
    can_sell_total = db.session.scalar(
        select(func.count()).select_from(BusinessProfile).where(
            BusinessProfile.can_sell.is_(True)
        )
    ) or 0
    can_buy_total = db.session.scalar(
        select(func.count()).select_from(BusinessProfile).where(
            BusinessProfile.can_buy.is_(True)
        )
    ) or 0
    products_total = db.session.scalar(
        select(func.count()).select_from(Product)
    ) or 0
    products_active = db.session.scalar(
        select(func.count()).select_from(Product).where(
            Product.product_status == "active"
        )
    ) or 0
    products_no_category = db.session.scalar(
        select(func.count()).select_from(Product).where(
            Product.category_id.is_(None)
        )
    ) or 0
    categories_total = db.session.scalar(
        select(func.count()).select_from(Category)
    ) or 0

    status_rows = db.session.execute(
        select(Order.order_status, func.count()).group_by(Order.order_status)
    ).all()
    orders_by_status = {
        status: int(count or 0) for status, count in status_rows
    }

    return {
        "users": {
            "total": int(users_total),
            "active": int(users_active),
        },
        "business_profiles": {
            "total": int(profiles_total),
            "can_buy": int(can_buy_total),
            "can_sell": int(can_sell_total),
        },
        "products": {
            "total": int(products_total),
            "active": int(products_active),
            "without_category": int(products_no_category),
        },
        "categories": {"total": int(categories_total)},
        "orders": {
            "total": sum(orders_by_status.values()),
            "pending": orders_by_status.get("pending", 0),
            "completed": orders_by_status.get("completed", 0),
            "cancelled": orders_by_status.get("cancelled", 0),
            "by_status": orders_by_status,
        },
    }


def _user_admin_payload(user: User, profile) -> dict:
    payload = user.to_dict()
    payload["has_profile"] = profile is not None
    if profile is not None:
        payload["business_profile"] = {
            "id": profile.id,
            "business_name": profile.business_name,
            "business_type": profile.business_type,
            "can_buy": bool(profile.can_buy),
            "can_sell": bool(profile.can_sell),
        }
    return payload


def list_users(args: dict, page: int, per_page: int) -> tuple[list, object]:
    statement = db.select(User).outerjoin(User.business_profile).options(
        db.joinedload(User.business_profile)
    )

    search = (args.get("q") or "").strip()
    if search:
        like = f"%{search}%"
        statement = statement.where(
            or_(
                User.full_name.ilike(like),
                User.email.ilike(like),
                BusinessProfile.business_name.ilike(like),
            )
        )

    role = (args.get("role") or "").strip()
    if role in ("business_user", "admin"):
        statement = statement.where(User.role == role)
    status = (args.get("status") or "").strip()
    if status in ("active", "suspended", "inactive"):
        statement = statement.where(User.account_status == status)
    capability = (args.get("capability") or "").strip()
    if capability == "seller":
        statement = statement.where(BusinessProfile.can_sell.is_(True))
    elif capability == "buyer":
        statement = statement.where(BusinessProfile.can_buy.is_(True))

    statement = statement.order_by(User.id.asc())
    pagination = db.paginate(
        statement, page=page, per_page=per_page, error_out=False
    )
    items = [_user_admin_payload(u, u.business_profile) for u in pagination.items]
    return items, pagination


def _get_user(user_id: int) -> User:
    user = db.session.scalar(db.select(User).where(User.id == user_id))
    if user is None:
        raise ApiError(
            "Pengguna tidak ditemukan.",
            status_code=404,
            code="user_not_found",
        )
    return user


def _update_capabilities(
    profile, data: dict, errors: dict[str, str]
) -> None:
    """Set can_buy dan can_sell; minimal satu harus tetap aktif."""
    current_buy = bool(profile.can_buy)
    current_sell = bool(profile.can_sell)

    target_buy = data.get("can_buy") if "can_buy" in data else current_buy
    target_sell = data.get("can_sell") if "can_sell" in data else current_sell

    for field, value in (("can_buy", target_buy), ("can_sell", target_sell)):
        if not isinstance(value, bool):
            errors[field] = "Nilai kemampuan harus true atau false."

    if errors:
        return

    if not (target_buy or target_sell):
        errors["can_buy"] = "Salah satu kemampuan harus tetap aktif."
        return

    if target_buy != current_buy:
        profile.can_buy = target_buy
    if target_sell != current_sell:
        profile.can_sell = target_sell


def update_user(admin_user: User, user_id: int, data: dict) -> dict:
    """Kelola pengguna: status akun, role, kemampuan beli/jual."""
    if not isinstance(data, dict):
        raise ApiError(
            "Body request harus berupa objek JSON yang valid.",
            status_code=400,
            code="invalid_json",
        )

    user = _get_user(user_id)
    errors: dict[str, str] = {}

    if "account_status" in data:
        status = data.get("account_status")
        if status not in ("active", "suspended", "inactive"):
            errors["account_status"] = "Pilihan: active, suspended, inactive."
        elif user.id == admin_user.id and status != "active":
            errors["account_status"] = (
                "Admin tidak dapat menonaktifkan akunnya sendiri."
            )
        elif status != user.account_status:
            user.account_status = status

    if "role" in data:
        new_role = data.get("role")
        if new_role not in ("business_user", "admin"):
            errors["role"] = "Pilihan: business_user, admin."
        elif user.id == admin_user.id and user.role == "admin" and new_role != "admin":
            errors["role"] = "Admin tidak dapat menurunkan role dirinya sendiri."
        elif new_role != user.role:
            user.role = new_role

    # Kemampuan akun via profil bisnis (hanya untuk business_user).
    profile = None
    if user.role == "business_user":
        profile = db.session.scalar(
            db.select(BusinessProfile).where(BusinessProfile.user_id == user.id)
        )
        if profile is not None and ("can_buy" in data or "can_sell" in data):
            _update_capabilities(profile, data, errors)

    if errors:
        db.session.rollback()
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)

    changed_status = "account_status" in data
    db.session.commit()

    if changed_status:
        create_notification(
            user_id=user.id,
            title="Status akun berubah",
            message=f"Status akun Anda diubah menjadi {user.account_status} oleh administrator.",
            type_="account",
            link="/pengaturan-akun",
            dedupe_key=f"account_status:{user.id}:{user.account_status}",
        )
        db.session.commit()

    db.session.refresh(user)
    profile = db.session.scalar(
        db.select(BusinessProfile).where(BusinessProfile.user_id == user.id)
    )
    return _user_admin_payload(user, profile)


def _category_payload(category: Category) -> dict:
    return {
        **category.to_dict(),
        "product_count": len(category.products),
        "children_count": len(category.children),
    }


def list_categories_admin(page: int, per_page: int) -> tuple[list, object]:
    statement = (
        db.select(Category)
        .options(
            db.selectinload(Category.products),
            db.selectinload(Category.children),
        )
        .order_by(Category.parent_id.asc(), Category.name.asc(), Category.id.asc())
    )
    pagination = db.paginate(
        statement, page=page, per_page=per_page, error_out=False
    )
    items = [_category_payload(c) for c in pagination.items]
    return items, pagination


def create_category(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ApiError(
            "Body request harus berupa objek JSON yang valid.",
            status_code=400,
            code="invalid_json",
        )
    name = (data.get("name") or "").strip()
    if not name:
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={"name": "Nama kategori wajib diisi."},
        )
    if len(name) > 120:
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={"name": "Nama kategori maksimal 120 karakter."},
        )
    description = (data.get("description") or "").strip() or None
    if description and len(description) > 500:
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={"description": "Deskripsi maksimal 500 karakter."},
        )

    parent_id = data.get("parent_id")
    if parent_id is not None:
        if not isinstance(parent_id, int):
            raise ApiError(
                "Validasi gagal.",
                status_code=422,
                errors={"parent_id": "parent_id harus berupa angka."},
            )
        parent = db.session.scalar(
            db.select(Category).where(Category.id == parent_id)
        )
        if parent is None:
            raise ApiError(
                "Validasi gagal.",
                status_code=422,
                errors={"parent_id": "Kategori induk tidak ditemukan."},
            )

    duplicate = db.session.scalar(
        db.select(Category).where(
            Category.name == name,
            Category.parent_id == parent_id,
        )
    )
    if duplicate is not None:
        raise ApiError(
            "Kategori dengan nama yang sama sudah ada.",
            status_code=409,
            code="category_duplicate",
        )

    category = Category(name=name, description=description, parent_id=parent_id)
    db.session.add(category)
    db.session.commit()
    db.session.refresh(category)
    return {**category.to_dict(), "product_count": 0, "children_count": 0}


def _get_category(category_id: int) -> Category:
    category = db.session.scalar(
        db.select(Category).where(Category.id == category_id)
    )
    if category is None:
        raise ApiError(
            "Kategori tidak ditemukan.",
            status_code=404,
            code="category_not_found",
        )
    return category


def update_category(category_id: int, data: dict) -> dict:
    category = _get_category(category_id)
    if not isinstance(data, dict):
        raise ApiError(
            "Body request harus berupa objek JSON yang valid.",
            status_code=400,
            code="invalid_json",
        )

    errors: dict[str, str] = {}
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            errors["name"] = "Nama kategori wajib diisi."
        elif len(name) > 120:
            errors["name"] = "Nama kategori maksimal 120 karakter."
        else:
            duplicate = db.session.scalar(
                db.select(Category).where(
                    Category.name == name,
                    Category.parent_id == category.parent_id,
                    Category.id != category.id,
                )
            )
            if duplicate is not None:
                errors["name"] = "Kategori dengan nama yang sama sudah ada."
            else:
                category.name = name

    if "description" in data:
        description = (data.get("description") or "").strip() or None
        if description and len(description) > 500:
            errors["description"] = "Deskripsi maksimal 500 karakter."
        else:
            category.description = description

    if errors:
        raise ApiError("Validasi gagal.", status_code=422, errors=errors)

    db.session.commit()
    db.session.refresh(category)
    return _category_payload(category)


def delete_category(category_id: int) -> dict:
    category = _get_category(category_id)
    product_count = len(category.products)
    children_count = len(category.children)
    if product_count or children_count:
        raise ApiError(
            "Kategori masih digunakan sehingga tidak dapat dihapus.",
            status_code=409,
            code="category_in_use",
            details={
                "products_related": product_count,
                "children_related": children_count,
            },
        )
    category_id = category.id
    db.session.delete(category)
    db.session.commit()
    return {"deleted": category_id}


def list_orders_admin(args: dict, page: int, per_page: int) -> tuple[list, object]:
    from services.order_service import serialize_order

    statement = db.select(Order).options(
        db.joinedload(Order.seller),
        db.joinedload(Order.buyer).joinedload(User.business_profile),
        db.selectinload(Order.items),
        db.selectinload(Order.payments),
    )

    status = (args.get("status") or "").strip()
    if status and status not in _ORDER_STATUSES:
        raise ApiError(
            "Filter status tidak valid.",
            status_code=422,
            errors={
                "status": "Pilihan: " + ", ".join(_ORDER_STATUSES) + "."
            },
        )
    if status:
        statement = statement.where(Order.order_status == status)

    search = (args.get("q") or "").strip()
    if search:
        statement = statement.where(
            Order.order_number.ilike(f"%{search}%")
        )

    sort = (args.get("sort") or "newest").strip()
    order_map = {
        "newest": (Order.created_at.desc(), Order.id.desc()),
        "oldest": (Order.created_at.asc(), Order.id.asc()),
        "total_desc": (Order.total_amount.desc(), Order.id.desc()),
        "total_asc": (Order.total_amount.asc(), Order.id.asc()),
    }
    statement = statement.order_by(*order_map.get(sort, order_map["newest"]))

    pagination = db.paginate(
        statement, page=page, per_page=per_page, error_out=False
    )
    items = [
        serialize_order(o, "admin", include_logs=False)
        for o in pagination.items
    ]
    return items, pagination
