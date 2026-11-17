"""Logika keranjang belanja pembeli."""

from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from extensions import db
from models import BusinessProfile, Cart, CartItem, Product, User
from utils.api_error import ApiError
from utils.order_validators import (
    MAX_UNSIGNED_INT,
    ensure_not_self_purchase,
    validate_cart_item_create_payload,
    validate_cart_item_update_payload,
)


def _cart_options():
    return [
        selectinload(Cart.items)
        .joinedload(CartItem.product)
        .joinedload(Product.business_profile),
        selectinload(Cart.items)
        .joinedload(CartItem.product)
        .joinedload(Product.inventory),
        selectinload(Cart.items)
        .joinedload(CartItem.product)
        .selectinload(Product.images),
    ]


def _lock_user(user_id: int) -> None:
    db.session.execute(
        select(User.id).where(User.id == user_id).with_for_update()
    ).scalar_one()


def _get_active_cart(user, *, for_update: bool = False, create: bool = False):
    stmt = (
        select(Cart)
        .where(Cart.buyer_id == user.id, Cart.status == "active")
        .order_by(Cart.id.desc())
    )
    if for_update:
        stmt = stmt.with_for_update()

    cart = db.session.scalar(stmt)
    if cart is None and create:
        cart = Cart(buyer_id=user.id, status="active")
        db.session.add(cart)
        db.session.flush()
    return cart


def _load_cart(cart_id: int):
    return db.session.scalar(
        select(Cart)
        .where(Cart.id == cart_id)
        .options(*_cart_options())
    )


def _empty_cart_payload() -> dict:
    return {
        "id": None,
        "status": "active",
        "created_at": None,
        "updated_at": None,
        "items": [],
        "summary": {
            "item_count": 0,
            "total_quantity": 0,
            "subtotal": 0.0,
            "seller_count": 0,
            "is_ready_for_checkout": False,
        },
    }


def _seller_payload(product: Product) -> dict | None:
    profile = product.business_profile
    if profile is None:
        return None
    return {
        "id": profile.id,
        "business_name": profile.business_name,
        "business_type": profile.business_type,
    }


def _image_url(product: Product) -> str | None:
    if product.product_status == "inactive":
        return None
    images = sorted(
        list(product.images),
        key=lambda image: (not bool(image.is_primary), image.id),
    )
    if not images:
        return None
    image = images[0]
    return f"/api/products/{int(product.id)}/images/{int(image.id)}/file"


def _available_quantity(product: Product) -> int:
    if product.inventory is None:
        return 0
    return int(product.inventory.available_quantity)


def _availability(product: Product, quantity: int) -> tuple[bool, str | None]:
    available = _available_quantity(product)

    if product.product_status == "inactive":
        return False, "Produk sedang tidak aktif."
    if product.product_status == "out_of_stock":
        return False, "Produk sedang ditandai tidak tersedia oleh penjual."
    if quantity < int(product.minimum_order):
        return (
            False,
            f"Minimum order produk ini adalah {int(product.minimum_order)} "
            f"{product.unit}.",
        )
    if available < quantity:
        return (
            False,
            f"Stok tersedia hanya {available} {product.unit}.",
        )
    return True, None


def _serialize_item(item: CartItem) -> dict:
    product = item.product
    quantity = int(item.quantity)

    if product is None:
        return {
            "id": item.id,
            "product_id": item.product_id,
            "quantity": quantity,
            "product_name": None,
            "price": None,
            "unit": None,
            "minimum_order": None,
            "product_status": None,
            "available_quantity": 0,
            "is_available": False,
            "availability_message": "Produk tidak ditemukan.",
            "seller": None,
            "image_url": None,
            "subtotal": 0.0,
            "created_at": item.created_at.isoformat()
            if item.created_at
            else None,
        }

    is_available, message = _availability(product, quantity)
    try:
        unit_price = Decimal(str(product.price)).quantize(Decimal("0.01"))
        subtotal = (unit_price * quantity).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        unit_price = Decimal("0.00")
        subtotal = Decimal("0.00")
        is_available = False
        message = "Harga produk tidak valid."

    return {
        "id": item.id,
        "product_id": item.product_id,
        "quantity": quantity,
        "product_name": product.product_name,
        "price": float(unit_price),
        "unit": product.unit,
        "minimum_order": int(product.minimum_order),
        "product_status": product.product_status,
        "available_quantity": _available_quantity(product),
        "is_available": is_available,
        "availability_message": message,
        "seller": _seller_payload(product),
        "image_url": _image_url(product),
        "subtotal": float(subtotal),
        "created_at": item.created_at.isoformat()
        if item.created_at
        else None,
    }


def serialize_cart(cart: Cart | None) -> dict:
    if cart is None:
        return _empty_cart_payload()

    items = [_serialize_item(item) for item in cart.items]
    total_quantity = sum(item["quantity"] for item in items)
    subtotal = sum(
        (Decimal(str(item["subtotal"])) for item in items),
        Decimal("0.00"),
    )
    seller_ids = {
        item["seller"]["id"]
        for item in items
        if item.get("seller") is not None
    }

    return {
        "id": cart.id,
        "status": cart.status,
        "created_at": cart.created_at.isoformat()
        if cart.created_at
        else None,
        "updated_at": cart.updated_at.isoformat()
        if cart.updated_at
        else None,
        "items": items,
        "summary": {
            "item_count": len(items),
            "total_quantity": total_quantity,
            "subtotal": float(subtotal.quantize(Decimal("0.01"))),
            "seller_count": len(seller_ids),
            "is_ready_for_checkout": bool(items)
            and all(item["is_available"] for item in items),
        },
    }


def get_cart(user) -> dict:
    cart = db.session.scalar(
        select(Cart)
        .where(Cart.buyer_id == user.id, Cart.status == "active")
        .order_by(Cart.id.desc())
        .options(*_cart_options())
    )
    return serialize_cart(cart)


def _validate_product_for_cart(product: Product, quantity: int) -> None:
    if product.product_status != "active":
        raise ApiError(
            "Produk tidak tersedia untuk dibeli.",
            status_code=422,
            errors={
                "product_id": "Produk sedang tidak aktif atau tidak tersedia."
            },
            code="product_unavailable",
            details={
                "product_id": product.id,
                "product_status": product.product_status,
            },
        )

    available = _available_quantity(product)
    if quantity < int(product.minimum_order):
        raise ApiError(
            "Jumlah tidak memenuhi minimum order.",
            status_code=422,
            errors={
                "quantity": (
                    f"Minimum order {int(product.minimum_order)} "
                    f"{product.unit}."
                )
            },
            code="minimum_order_not_met",
            details={
                "minimum_order": int(product.minimum_order),
                "quantity": quantity,
            },
        )

    if available < quantity:
        raise ApiError(
            "Stok tidak mencukupi.",
            status_code=422,
            errors={
                "quantity": (
                    f"Stok tersedia hanya {available} {product.unit}."
                )
            },
            code="insufficient_stock",
            details={
                "available_quantity": available,
                "requested_quantity": quantity,
            },
        )


def add_cart_item(user, data: dict) -> dict:
    values = validate_cart_item_create_payload(data)

    # Kemampuan membeli: akun yang menonaktifkan can_buy tidak dapat
    # menambahkan produk ke keranjang.
    buyer_profile = db.session.scalar(
        select(BusinessProfile).where(BusinessProfile.user_id == user.id)
    )
    if buyer_profile is not None and not buyer_profile.can_buy:
        raise ApiError(
            "Kemampuan membeli dinonaktifkan untuk akun ini.",
            status_code=403,
            code="buy_capability_disabled",
        )

    try:
        _lock_user(user.id)
        cart = _get_active_cart(user, for_update=True, create=True)

        existing = db.session.scalar(
            select(CartItem)
            .where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == values["product_id"],
            )
            .with_for_update()
        )
        product = db.session.scalar(
            select(Product)
            .where(Product.id == values["product_id"])
            .with_for_update()
        )
        if product is None:
            raise ApiError(
                "Produk tidak ditemukan.",
                status_code=404,
                code="product_not_found",
            )

        ensure_not_self_purchase(
            buyer=user,
            seller_profile_id=product.business_id,
        )

        requested_quantity = values["quantity"]
        new_quantity = (
            int(existing.quantity) + requested_quantity
            if existing is not None
            else requested_quantity
        )
        if new_quantity > MAX_UNSIGNED_INT:
            raise ApiError(
                "Jumlah produk melebihi batas maksimum.",
                status_code=422,
                errors={"quantity": f"Maksimal {MAX_UNSIGNED_INT}."},
                code="quantity_overflow",
            )

        _validate_product_for_cart(product, new_quantity)

        if existing is not None:
            existing.quantity = new_quantity
        else:
            db.session.add(
                CartItem(
                    cart_id=cart.id,
                    product_id=product.id,
                    quantity=new_quantity,
                )
            )

        db.session.commit()
        cart = _load_cart(cart.id)
        return serialize_cart(cart)
    except ApiError:
        db.session.rollback()
        raise
    except IntegrityError as exc:
        db.session.rollback()
        raise ApiError(
            "Produk tidak dapat ditambahkan ke keranjang.",
            status_code=409,
            code="cart_item_conflict",
        ) from exc


def update_cart_item(user, item_id: int, data: dict) -> dict:
    values = validate_cart_item_update_payload(data)

    try:
        _lock_user(user.id)
        cart = _get_active_cart(user, for_update=True)
        if cart is None:
            raise ApiError(
                "Item keranjang tidak ditemukan.",
                status_code=404,
                code="cart_item_not_found",
            )

        item = db.session.scalar(
            select(CartItem)
            .where(CartItem.id == item_id, CartItem.cart_id == cart.id)
            .with_for_update()
        )
        if item is None:
            raise ApiError(
                "Item keranjang tidak ditemukan.",
                status_code=404,
                code="cart_item_not_found",
            )

        product = db.session.scalar(
            select(Product)
            .where(Product.id == item.product_id)
            .with_for_update()
        )
        if product is None:
            raise ApiError(
                "Produk tidak ditemukan.",
                status_code=404,
                code="product_not_found",
            )

        ensure_not_self_purchase(
            buyer=user,
            seller_profile_id=product.business_id,
        )

        _validate_product_for_cart(product, values["quantity"])
        item.quantity = values["quantity"]

        db.session.commit()
        cart = _load_cart(cart.id)
        return serialize_cart(cart)
    except ApiError:
        db.session.rollback()
        raise


def delete_cart_item(user, item_id: int) -> dict:
    try:
        _lock_user(user.id)
        cart = _get_active_cart(user, for_update=True)
        if cart is None:
            raise ApiError(
                "Item keranjang tidak ditemukan.",
                status_code=404,
                code="cart_item_not_found",
            )

        item = db.session.scalar(
            select(CartItem)
            .where(CartItem.id == item_id, CartItem.cart_id == cart.id)
            .with_for_update()
        )
        if item is None:
            raise ApiError(
                "Item keranjang tidak ditemukan.",
                status_code=404,
                code="cart_item_not_found",
            )

        db.session.delete(item)
        db.session.commit()
        cart = _load_cart(cart.id)
        return serialize_cart(cart)
    except ApiError:
        db.session.rollback()
        raise
