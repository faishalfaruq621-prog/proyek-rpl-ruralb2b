"""Logika katalog produk, inventori, dan gambar produk."""

from flask import current_app
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from extensions import db
from models import BusinessProfile, Category, Inventory, Product, ProductImage
from services.business_profile_service import get_profile_for_user
from services.product_image_storage_service import (
    delete_product_image,
    image_mimetype,
    normalize_primary_flag,
    resolve_product_image,
    safe_image_download_name,
    save_product_image,
)
from utils.api_error import ApiError
from utils.product_validators import (
    MAX_UNSIGNED_INT,
    PRODUCT_STATUSES,
    validate_bool_filter,
    validate_inventory_payload,
    validate_price_filter,
    validate_positive_int_filter,
    validate_product_payload,
    validate_sort,
    validate_text_filter,
)


def _product_options(include_images: bool = True):
    options = [
        joinedload(Product.business_profile),
        joinedload(Product.category),
        joinedload(Product.inventory),
    ]
    if include_images:
        options.append(selectinload(Product.images))
    return options


def _public_visibility():
    return Product.product_status != "inactive"


def _resolve_category(category_id: int | None) -> Category | None:
    if category_id is None:
        return None

    category = db.session.get(Category, category_id)
    if category is None:
        raise ApiError(
            "Kategori tidak ditemukan.",
            status_code=422,
            errors={"category_id": "Kategori yang dipilih tidak tersedia."},
            code="category_not_found",
        )
    return category


def _location_payload(profile: BusinessProfile | None) -> dict:
    if profile is None:
        return {
            "village": None,
            "district": None,
            "city": None,
            "province": None,
            "postal_code": None,
        }

    return {
        "village": profile.village,
        "district": profile.district,
        "city": profile.city,
        "province": profile.province,
        "postal_code": profile.postal_code,
    }


def _seller_payload(profile: BusinessProfile | None) -> dict | None:
    if profile is None:
        return None

    return {
        "id": profile.id,
        "business_name": profile.business_name,
        "business_type": profile.business_type,
    }


def _image_url(audience: str, product_id: int, image_id: int) -> str:
    prefix = "/api/business/products" if audience == "business" else "/api/products"
    return f"{prefix}/{int(product_id)}/images/{int(image_id)}/file"


def _image_payload(image: ProductImage, audience: str) -> dict:
    payload = image.to_dict()
    payload["url"] = _image_url(audience, image.product_id, image.id)
    return payload


def _inventory_payload(product: Product) -> dict:
    if product.inventory is None:
        return {
            "id": None,
            "product_id": product.id,
            "stock_quantity": 0,
            "reserved_quantity": 0,
            "available_quantity": 0,
            "in_stock": False,
            "updated_at": None,
        }
    return product.inventory.to_dict()


def serialize_product(product: Product, audience: str = "public") -> dict:
    payload = product.to_dict()
    inventory = _inventory_payload(product)

    images = sorted(
        list(product.images),
        key=lambda image: (not bool(image.is_primary), image.id),
    )

    payload.update(
        {
            "category": (
                {
                    "id": product.category.id,
                    "name": product.category.name,
                }
                if product.category is not None
                else None
            ),
            "seller": _seller_payload(product.business_profile),
            "location": _location_payload(product.business_profile),
            "inventory": inventory,
            "stock_quantity": inventory["stock_quantity"],
            "available_quantity": inventory["available_quantity"],
            "is_in_stock": inventory["in_stock"],
            "images": [_image_payload(image, audience) for image in images],
        }
    )
    return payload


def _apply_public_filters(stmt, args):
    raw_q = args.get("q")
    if raw_q is None:
        raw_q = args.get("search")
    q = validate_text_filter(raw_q, "q", "Pencarian", 180)

    raw_category = args.get("category_id")
    if raw_category is None:
        raw_category = args.get("category")
    category_id = validate_positive_int_filter(
        raw_category, "category_id", "Kategori"
    )
    min_price = validate_price_filter(
        args.get("min_price"), "min_price", "Harga minimum"
    )
    max_price = validate_price_filter(
        args.get("max_price"), "max_price", "Harga maksimum"
    )
    location = validate_text_filter(
        args.get("location"), "location", "Lokasi", 120
    )
    city = validate_text_filter(args.get("city"), "city", "Kota", 120)
    province = validate_text_filter(
        args.get("province"), "province", "Provinsi", 120
    )
    district = validate_text_filter(
        args.get("district"), "district", "Kecamatan", 120
    )
    village = validate_text_filter(args.get("village"), "village", "Desa", 120)

    if min_price is not None and max_price is not None and min_price > max_price:
        raise ApiError(
            "Rentang harga tidak valid.",
            status_code=422,
            errors={"max_price": "Harga maksimum harus >= harga minimum."},
        )

    if q:
        stmt = stmt.where(Product.product_name.ilike(f"%{q}%"))
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)

    location_filters = []
    if location:
        pattern = f"%{location}%"
        location_filters.extend(
            [
                BusinessProfile.village.ilike(pattern),
                BusinessProfile.district.ilike(pattern),
                BusinessProfile.city.ilike(pattern),
                BusinessProfile.province.ilike(pattern),
            ]
        )
    if city:
        location_filters.append(BusinessProfile.city.ilike(f"%{city}%"))
    if province:
        location_filters.append(
            BusinessProfile.province.ilike(f"%{province}%")
        )
    if district:
        location_filters.append(
            BusinessProfile.district.ilike(f"%{district}%")
        )
    if village:
        location_filters.append(BusinessProfile.village.ilike(f"%{village}%"))

    if location_filters:
        stmt = stmt.join(
            BusinessProfile, Product.business_id == BusinessProfile.id
        ).where(or_(*location_filters))

    raw_in_stock = args.get("in_stock")
    if raw_in_stock is None:
        raw_in_stock = args.get("available")
    if raw_in_stock is None:
        raw_in_stock = args.get("stock")
    in_stock = validate_bool_filter(
        raw_in_stock, "in_stock", "Ketersediaan stok"
    )

    if in_stock is not None:
        stmt = stmt.outerjoin(
            Inventory, Inventory.product_id == Product.id
        )
        available_expression = func.coalesce(
            Inventory.stock_quantity, 0
        ) - func.coalesce(Inventory.reserved_quantity, 0)
        if in_stock:
            stmt = stmt.where(available_expression > 0)
        else:
            stmt = stmt.where(available_expression <= 0)

    return stmt


def _sort_order(sort: str):
    mapping = {
        "newest": [Product.created_at.desc(), Product.id.desc()],
        "oldest": [Product.created_at.asc(), Product.id.asc()],
        "price_asc": [Product.price.asc(), Product.id.asc()],
        "price_desc": [Product.price.desc(), Product.id.desc()],
        "name_asc": [Product.product_name.asc(), Product.id.asc()],
        "name_desc": [Product.product_name.desc(), Product.id.desc()],
    }
    return mapping[sort]


def list_public_products(args, page: int, per_page: int):
    stmt = select(Product).where(_public_visibility())
    stmt = _apply_public_filters(stmt, args)
    sort = validate_sort(args.get("sort"))
    stmt = stmt.options(*_product_options()).order_by(*_sort_order(sort))

    pagination = db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        error_out=False,
    )
    items = [serialize_product(product, "public") for product in pagination.items]
    return items, pagination


def get_public_product(product_id: int) -> dict:
    product = db.session.scalar(
        select(Product)
        .where(Product.id == product_id, _public_visibility())
        .options(*_product_options())
    )
    if product is None:
        raise ApiError(
            "Produk tidak ditemukan.",
            status_code=404,
            code="product_not_found",
        )
    return serialize_product(product, "public")


def list_categories(parent_id: int | None = None) -> list[dict]:
    stmt = select(Category).order_by(Category.name.asc(), Category.id.asc())
    if parent_id is not None:
        stmt = stmt.where(Category.parent_id == parent_id)
    return [category.to_dict() for category in db.session.scalars(stmt).all()]


def _parse_business_status(args) -> str | None:
    raw_status = args.get("status")
    if raw_status is None:
        raw_status = args.get("product_status")
    if raw_status is None:
        return None
    if not isinstance(raw_status, str):
        raise ApiError(
            "Filter status tidak valid.",
            status_code=422,
            errors={"status": "Filter status harus berupa teks."},
        )
    status = raw_status.strip().lower()
    if not status:
        return None
    if status not in PRODUCT_STATUSES:
        raise ApiError(
            "Filter status tidak valid.",
            status_code=422,
            errors={
                "status": "Pilihan: " + ", ".join(sorted(PRODUCT_STATUSES)) + "."
            },
        )
    return status


def _apply_business_filters(stmt, args):
    raw_q = args.get("q")
    if raw_q is None:
        raw_q = args.get("search")
    q = validate_text_filter(raw_q, "q", "Pencarian", 180)

    status = _parse_business_status(args)

    raw_category = args.get("category_id")
    if raw_category is None:
        raw_category = args.get("category")
    category_id = validate_positive_int_filter(
        raw_category, "category_id", "Kategori"
    )

    if q:
        stmt = stmt.where(Product.product_name.ilike(f"%{q}%"))
    if status is not None:
        stmt = stmt.where(Product.product_status == status)
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)

    raw_in_stock = args.get("in_stock")
    if raw_in_stock is None:
        raw_in_stock = args.get("available")
    if raw_in_stock is None:
        raw_in_stock = args.get("stock")
    in_stock = validate_bool_filter(
        raw_in_stock, "in_stock", "Ketersediaan stok"
    )
    if in_stock is not None:
        stmt = stmt.outerjoin(
            Inventory, Inventory.product_id == Product.id
        )
        available_expression = func.coalesce(
            Inventory.stock_quantity, 0
        ) - func.coalesce(Inventory.reserved_quantity, 0)
        stmt = stmt.where(
            available_expression > 0 if in_stock else available_expression <= 0
        )

    return stmt


def list_business_products(user, args, page: int, per_page: int):
    profile = get_profile_for_user(user)
    stmt = select(Product).where(Product.business_id == profile.id)
    stmt = _apply_business_filters(stmt, args)
    sort = validate_sort(args.get("sort"))
    stmt = stmt.options(*_product_options()).order_by(*_sort_order(sort))

    pagination = db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        error_out=False,
    )
    items = [
        serialize_product(product, "business") for product in pagination.items
    ]
    return items, pagination


def list_business_inventory(user, args, page: int, per_page: int):
    profile = get_profile_for_user(user)
    stmt = select(Product).where(Product.business_id == profile.id)
    stmt = _apply_business_filters(stmt, args)
    sort = validate_sort(args.get("sort"))
    stmt = stmt.options(*_product_options()).order_by(*_sort_order(sort))

    pagination = db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        error_out=False,
    )
    items = [
        serialize_product(product, "business") for product in pagination.items
    ]
    return items, pagination


def _get_owned_product(
    user,
    product_id: int,
    *,
    for_update: bool = False,
    include_images: bool = True,
):
    profile = get_profile_for_user(user)
    stmt = select(Product).where(
        Product.id == product_id,
        Product.business_id == profile.id,
    )
    if for_update:
        stmt = stmt.with_for_update()
    stmt = stmt.options(*_product_options(include_images=include_images))

    product = db.session.scalar(stmt)
    if product is None:
        raise ApiError(
            "Produk tidak ditemukan.",
            status_code=404,
            code="product_not_found",
        )
    return product, profile


def get_business_product(user, product_id: int) -> dict:
    product, _profile = _get_owned_product(user, product_id)
    return serialize_product(product, "business")


def create_product(user, data: dict) -> dict:
    profile = get_profile_for_user(user)
    if not profile.can_sell:
        raise ApiError(
            "Kemampuan menjual dinonaktifkan untuk akun ini.",
            status_code=403,
            code="sell_capability_disabled",
        )
    values = validate_product_payload(data, partial=False, allow_stock=True)
    stock_quantity = values.pop("stock_quantity", 0)
    category = _resolve_category(values.pop("category_id", None))

    product = Product(
        business_id=profile.id,
        category_id=category.id if category is not None else None,
        product_name=values["product_name"],
        description=values.get("description"),
        price=values["price"],
        unit=values["unit"],
        minimum_order=values["minimum_order"],
        product_status=values["product_status"],
    )
    db.session.add(product)
    db.session.flush()

    inventory = Inventory(
        product_id=product.id,
        stock_quantity=stock_quantity,
        reserved_quantity=0,
    )
    db.session.add(inventory)
    db.session.commit()

    product = db.session.scalar(
        select(Product)
        .where(Product.id == product.id)
        .options(*_product_options())
    )
    return serialize_product(product, "business")


def update_product(user, product_id: int, data: dict, partial: bool) -> dict:
    product, _profile = _get_owned_product(
        user, product_id, for_update=True, include_images=False
    )
    values = validate_product_payload(
        data, partial=partial, allow_stock=False
    )

    if "category_id" in values:
        category = _resolve_category(values.pop("category_id"))
        product.category_id = category.id if category is not None else None

    for field in (
        "product_name",
        "description",
        "price",
        "unit",
        "minimum_order",
        "product_status",
    ):
        if field in values:
            setattr(product, field, values[field])

    db.session.commit()

    product = db.session.scalar(
        select(Product)
        .where(Product.id == product.id)
        .options(*_product_options())
    )
    return serialize_product(product, "business")


def _reference_counts(product_id: int) -> dict:
    order_items = db.session.execute(
        db.text(
            "SELECT COUNT(*) FROM order_items WHERE product_id = :product_id"
        ),
        {"product_id": product_id},
    ).scalar_one()
    cart_items = db.session.execute(
        db.text(
            "SELECT COUNT(*) FROM cart_items WHERE product_id = :product_id"
        ),
        {"product_id": product_id},
    ).scalar_one()
    return {
        "order_items": int(order_items or 0),
        "cart_items": int(cart_items or 0),
    }


def delete_product(user, product_id: int) -> None:
    product, _profile = _get_owned_product(
        user, product_id, for_update=True, include_images=True
    )

    references = _reference_counts(product.id)
    if references["order_items"] or references["cart_items"]:
        raise ApiError(
            "Produk tidak dapat dihapus karena sudah dipakai pada keranjang "
            "atau pesanan. Nonaktifkan produk sebagai gantinya.",
            status_code=409,
            code="product_in_use",
            details=references,
        )

    inventory = db.session.scalar(
        select(Inventory)
        .where(Inventory.product_id == product.id)
        .with_for_update()
    )
    image_paths = [image.image_path for image in product.images]

    try:
        if inventory is not None:
            db.session.delete(inventory)
        for image in list(product.images):
            db.session.delete(image)
        db.session.delete(product)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ApiError(
            "Produk tidak dapat dihapus karena masih direferensikan data lain.",
            status_code=409,
            code="product_in_use",
        ) from exc

    for image_path in image_paths:
        delete_product_image(image_path)


def add_product_image(
    user,
    product_id: int,
    file_storage,
    is_primary_raw=None,
) -> dict:
    product, _profile = _get_owned_product(
        user, product_id, for_update=True, include_images=True
    )

    max_images = int(current_app.config["MAX_PRODUCT_IMAGES"])
    if len(product.images) >= max_images:
        raise ApiError(
            "Batas jumlah gambar produk tercapai.",
            status_code=409,
            code="image_limit_reached",
            details={"max_images": max_images},
        )

    is_primary = normalize_primary_flag(is_primary_raw)
    make_primary = is_primary or not product.images
    relative_path = save_product_image(file_storage, product.id)

    try:
        if make_primary:
            for image in product.images:
                image.is_primary = False

        image = ProductImage(
            product_id=product.id,
            image_path=relative_path,
            is_primary=make_primary,
        )
        db.session.add(image)
        db.session.commit()
        db.session.refresh(image)
    except Exception:
        db.session.rollback()
        delete_product_image(relative_path)
        raise

    return _image_payload(image, "business")


def delete_product_image_record(user, product_id: int, image_id: int) -> None:
    product, _profile = _get_owned_product(
        user, product_id, for_update=True, include_images=True
    )

    image = db.session.scalar(
        select(ProductImage).where(
            ProductImage.id == image_id,
            ProductImage.product_id == product.id,
        )
    )
    if image is None:
        raise ApiError(
            "Gambar produk tidak ditemukan.",
            status_code=404,
            code="product_image_not_found",
        )

    image_path = image.image_path
    remaining = [item for item in product.images if item.id != image.id]

    try:
        db.session.delete(image)
        if image.is_primary and remaining:
            new_primary = min(remaining, key=lambda item: item.id)
            for item in remaining:
                item.is_primary = item.id == new_primary.id
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    delete_product_image(image_path)


def get_public_image_file(product_id: int, image_id: int):
    image = db.session.scalar(
        select(ProductImage)
        .join(Product, Product.id == ProductImage.product_id)
        .where(
            ProductImage.id == image_id,
            ProductImage.product_id == product_id,
            _public_visibility(),
        )
    )
    if image is None:
        raise ApiError(
            "Gambar produk tidak ditemukan.",
            status_code=404,
            code="product_image_not_found",
        )

    path = resolve_product_image(image.image_path)
    return (
        path,
        safe_image_download_name(product_id, image.id, image.image_path),
        image_mimetype(image.image_path),
    )


def get_business_image_file(user, product_id: int, image_id: int):
    profile = get_profile_for_user(user)
    image = db.session.scalar(
        select(ProductImage)
        .join(Product, Product.id == ProductImage.product_id)
        .where(
            ProductImage.id == image_id,
            ProductImage.product_id == product_id,
            Product.business_id == profile.id,
        )
    )
    if image is None:
        raise ApiError(
            "Gambar produk tidak ditemukan.",
            status_code=404,
            code="product_image_not_found",
        )

    path = resolve_product_image(image.image_path)
    return (
        path,
        safe_image_download_name(product_id, image.id, image.image_path),
        image_mimetype(image.image_path),
    )


def update_inventory(user, product_id: int, data: dict) -> dict:
    product, _profile = _get_owned_product(
        user, product_id, for_update=True, include_images=False
    )
    values = validate_inventory_payload(data)

    inventory = db.session.scalar(
        select(Inventory)
        .where(Inventory.product_id == product.id)
        .with_for_update()
    )
    if inventory is None:
        inventory = Inventory(
            product_id=product.id,
            stock_quantity=0,
            reserved_quantity=0,
        )
        db.session.add(inventory)
        db.session.flush()

    if "stock_quantity" in values:
        new_stock = values["stock_quantity"]
    else:
        new_stock = int(inventory.stock_quantity) + values["adjustment"]

    if new_stock < 0:
        raise ApiError(
            "Stok tidak boleh negatif.",
            status_code=422,
            errors={"stock_quantity": "Stok akhir minimal 0."},
            code="negative_stock",
        )

    if new_stock > MAX_UNSIGNED_INT:
        raise ApiError(
            "Stok melebihi batas maksimum.",
            status_code=422,
            errors={"stock_quantity": f"Maksimal {MAX_UNSIGNED_INT}."},
            code="stock_overflow",
        )

    if new_stock < int(inventory.reserved_quantity):
        raise ApiError(
            "Stok tidak boleh lebih kecil dari jumlah yang sudah direservasi.",
            status_code=422,
            errors={
                "stock_quantity": (
                    f"Stok minimal {int(inventory.reserved_quantity)} "
                    "karena ada reservasi."
                )
            },
            code="stock_below_reserved",
            details={"reserved_quantity": int(inventory.reserved_quantity)},
        )

    inventory.stock_quantity = new_stock
    db.session.commit()
    db.session.refresh(inventory)

    product = db.session.scalar(
        select(Product)
        .where(Product.id == product.id)
        .options(*_product_options())
    )
    return {
        "inventory": inventory.to_dict(),
        "product": serialize_product(product, "business"),
    }
