"""Logika checkout, pesanan pembeli, dan pengelolaan pesanan penjual."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from extensions import db
from models import (
    Cart,
    CartItem,
    Inventory,
    Order,
    OrderItem,
    OrderStatusLog,
    Payment,
    Product,
    User,
    BusinessProfile,
)
from services.business_profile_service import get_profile_for_user
from services.notification_service import create_notification
from utils.api_error import ApiError
from utils.order_validators import (
    BUYER_CANCELLABLE_STATUSES,
    MAX_UNSIGNED_INT,
    SELLER_STATUS_TRANSITIONS,
    ensure_not_self_purchase,
    validate_cancel_payload,
    validate_checkout_payload,
    validate_order_filter_status,
    validate_order_search,
    validate_order_sort,
    validate_order_status_payload,
    validate_order_total,
)


def _profile_user_id(seller_profile_id: int | None) -> int | None:
    """user_id pemilik profil bisnis penjual (untuk notifikasi)."""
    if seller_profile_id is None:
        return None
    return db.session.scalar(
        select(BusinessProfile.user_id).where(
            BusinessProfile.id == seller_profile_id
        )
    )


def _order_options(include_logs: bool = True):
    options = [
        joinedload(Order.seller),
        joinedload(Order.buyer).joinedload(User.business_profile),
        selectinload(Order.items).joinedload(OrderItem.product),
        selectinload(Order.payments),
    ]
    if include_logs:
        options.append(
            selectinload(Order.status_logs).joinedload(
                OrderStatusLog.changed_by_user
            )
        )
    return options


def _seller_payload(profile) -> dict | None:
    if profile is None:
        return None
    return {
        "id": profile.id,
        "business_name": profile.business_name,
        "business_type": profile.business_type,
    }


def _buyer_payload(user: User | None) -> dict | None:
    if user is None:
        return None
    profile = user.business_profile
    return {
        "id": user.id,
        "full_name": user.full_name,
        "business_name": profile.business_name if profile else None,
    }


def serialize_payment(payment: Payment | None) -> dict | None:
    if payment is None:
        return None
    return {
        "id": payment.id,
        "order_id": payment.order_id,
        "payment_method": payment.payment_method,
        "payment_reference": payment.payment_reference,
        "payment_status": payment.payment_status,
        "amount": float(payment.amount)
        if payment.amount is not None
        else None,
        "paid_at": payment.paid_at.isoformat()
        if payment.paid_at
        else None,
        "created_at": payment.created_at.isoformat()
        if payment.created_at
        else None,
    }


def _serialize_order_item(item: OrderItem) -> dict:
    price = float(item.price_snapshot)
    return {
        "id": item.id,
        "product_id": item.product_id,
        "product_name": item.product_name,
        "price_snapshot": price,
        "price": price,
        "quantity": int(item.quantity),
        "subtotal": float(item.subtotal),
        "unit": item.product.unit if item.product is not None else None,
    }


def serialize_order(
    order: Order,
    viewer_role: str,
    include_logs: bool = True,
) -> dict:
    payments = list(order.payments)
    latest_payment = payments[-1] if payments else None
    items = [_serialize_order_item(item) for item in order.items]

    payload = {
        "id": order.id,
        "order_number": order.order_number,
        "buyer_id": order.buyer_id,
        "seller_id": order.seller_id,
        "total_amount": float(order.total_amount)
        if order.total_amount is not None
        else None,
        "shipping_address": order.shipping_address,
        "buyer_note": order.buyer_note,
        "order_status": order.order_status,
        "created_at": order.created_at.isoformat()
        if order.created_at
        else None,
        "updated_at": order.updated_at.isoformat()
        if order.updated_at
        else None,
        "buyer": _buyer_payload(order.buyer),
        "seller": _seller_payload(order.seller),
        "items": items,
        "item_count": len(items),
        "total_quantity": sum(item["quantity"] for item in items),
        "payment": serialize_payment(latest_payment),
        "payments": [serialize_payment(payment) for payment in payments],
        "can_cancel": (
            viewer_role == "buyer"
            and order.order_status in BUYER_CANCELLABLE_STATUSES
        ),
        # Konfirmasi penerimaan barang oleh pembeli (shipped -> completed).
        "can_receive": (
            viewer_role == "buyer" and order.order_status == "shipped"
        ),
        "allowed_next_statuses": (
            SELLER_STATUS_TRANSITIONS.get(order.order_status, [])
            if viewer_role == "seller"
            else []
        ),
    }

    if include_logs:
        payload["status_logs"] = [
            {
                "id": log.id,
                "old_status": log.old_status,
                "new_status": log.new_status,
                "notes": log.notes,
                "changed_by": log.changed_by,
                "changed_by_name": (
                    log.changed_by_user.full_name
                    if log.changed_by_user is not None
                    else None
                ),
                "created_at": log.created_at.isoformat()
                if log.created_at
                else None,
            }
            for log in order.status_logs
        ]

    return payload


def _reload_order(order_id: int, include_logs: bool = True):
    order = db.session.scalar(
        select(Order)
        .where(Order.id == order_id)
        .options(*_order_options(include_logs=include_logs))
    )
    if order is None:
        raise ApiError(
            "Pesanan tidak ditemukan.",
            status_code=404,
            code="order_not_found",
        )
    return order


def _get_buyer_order(
    user,
    order_id: int,
    *,
    for_update: bool = False,
    include_logs: bool = True,
):
    stmt = select(Order).where(
        Order.id == order_id,
        Order.buyer_id == user.id,
    )
    if for_update:
        # Segarkan instance dari baris terkunci agar status/total yang
        # divalidasi selalu nilai terbaru di database, bukan cache lama.
        stmt = stmt.with_for_update().execution_options(
            populate_existing=True
        )
    else:
        stmt = stmt.options(*_order_options(include_logs=include_logs))
    order = db.session.scalar(stmt)
    if order is None:
        raise ApiError(
            "Pesanan tidak ditemukan.",
            status_code=404,
            code="order_not_found",
        )
    return order


def _get_seller_order(
    user,
    order_id: int,
    *,
    for_update: bool = False,
    include_logs: bool = True,
):
    profile = get_profile_for_user(user)
    if not profile.can_sell:
        raise ApiError(
            "Kemampuan menjual dinonaktifkan untuk akun ini.",
            status_code=403,
            code="sell_capability_disabled",
        )
    stmt = select(Order).where(
        Order.id == order_id,
        Order.seller_id == profile.id,
    )
    if for_update:
        # Segarkan instance dari baris terkunci agar status/total yang
        # divalidasi selalu nilai terbaru di database, bukan cache lama.
        stmt = stmt.with_for_update().execution_options(
            populate_existing=True
        )
    else:
        stmt = stmt.options(*_order_options(include_logs=include_logs))

    order = db.session.scalar(stmt)
    if order is None:
        raise ApiError(
            "Pesanan tidak ditemukan.",
            status_code=404,
            code="order_not_found",
        )
    return order


def _order_number() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"RBB2B-{timestamp}-{uuid4().hex[:10].upper()}"


def _shipping_address(user, values: dict) -> str:
    if values.get("shipping_address"):
        return values["shipping_address"]

    profile = get_profile_for_user(user)
    parts = [
        profile.address,
        profile.village,
        profile.district,
        profile.city,
        profile.province,
        profile.postal_code,
    ]
    address = ", ".join(part for part in parts if part)
    if not address:
        raise ApiError(
            "Alamat pengiriman wajib diisi.",
            status_code=422,
            errors={
                "shipping_address": (
                    "Kirim shipping_address atau lengkapi alamat profil bisnis."
                )
            },
            code="shipping_address_required",
        )
    return address


def _order_by_clause(sort: str):
    if sort == "oldest":
        return [Order.created_at.asc(), Order.id.asc()]
    return [Order.created_at.desc(), Order.id.desc()]


def _apply_order_filters(stmt, args, *, seller_view: bool):
    raw_status = args.get("status")
    if raw_status is None:
        raw_status = args.get("order_status")
    status = validate_order_filter_status(raw_status)
    q = validate_order_search(args.get("q") or args.get("search"))

    if status is not None:
        stmt = stmt.where(Order.order_status == status)

    if q:
        pattern = f"%{q}%"
        if seller_view:
            stmt = stmt.join(User, Order.buyer_id == User.id).where(
                or_(
                    Order.order_number.ilike(pattern),
                    User.full_name.ilike(pattern),
                )
            )
        else:
            stmt = stmt.where(Order.order_number.ilike(pattern))

    return stmt


def list_buyer_orders(user, args, page: int, per_page: int):
    stmt = select(Order).where(Order.buyer_id == user.id)
    stmt = _apply_order_filters(stmt, args, seller_view=False)
    sort = validate_order_sort(args.get("sort"))
    stmt = stmt.options(*_order_options(include_logs=False)).order_by(
        *_order_by_clause(sort)
    )

    pagination = db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        error_out=False,
    )
    items = [
        serialize_order(order, "buyer", include_logs=False)
        for order in pagination.items
    ]
    return items, pagination


def list_seller_orders(user, args, page: int, per_page: int):
    profile = get_profile_for_user(user)
    if not profile.can_sell:
        raise ApiError(
            "Kemampuan menjual dinonaktifkan untuk akun ini.",
            status_code=403,
            code="sell_capability_disabled",
        )
    stmt = select(Order).where(Order.seller_id == profile.id)
    stmt = _apply_order_filters(stmt, args, seller_view=True)
    sort = validate_order_sort(args.get("sort"))
    stmt = stmt.options(*_order_options(include_logs=False)).order_by(
        *_order_by_clause(sort)
    )

    pagination = db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        error_out=False,
    )
    items = [
        serialize_order(order, "seller", include_logs=False)
        for order in pagination.items
    ]
    return items, pagination


def get_buyer_order(user, order_id: int) -> dict:
    order = _get_buyer_order(user, order_id, include_logs=True)
    return serialize_order(order, "buyer", include_logs=True)


def get_seller_order(user, order_id: int) -> dict:
    order = _get_seller_order(user, order_id, include_logs=True)
    return serialize_order(order, "seller", include_logs=True)


def _checkout_error(code: str, message: str, items: list[dict]):
    raise ApiError(
        message,
        status_code=409 if code != "minimum_order_not_met" else 422,
        code=code,
        details={"items": items},
    )


def checkout(user, data: dict) -> list[dict]:
    values = validate_checkout_payload(data)

    # Kemampuan membeli: akun dengan profil yang menonaktifkan can_buy
    # tidak dapat melakukan transaksi baru.
    profile = db.session.scalar(
        select(BusinessProfile).where(BusinessProfile.user_id == user.id)
    )
    if profile is not None and not profile.can_buy:
        raise ApiError(
            "Kemampuan membeli dinonaktifkan untuk akun ini.",
            status_code=403,
            code="buy_capability_disabled",
        )

    try:
        db.session.execute(
            select(User.id).where(User.id == user.id).with_for_update()
        ).scalar_one()

        cart = db.session.scalar(
            select(Cart)
            .where(Cart.buyer_id == user.id, Cart.status == "active")
            .order_by(Cart.id.desc())
            .with_for_update()
        )
        if cart is None:
            raise ApiError(
                "Keranjang belanja kosong.",
                status_code=422,
                code="cart_empty",
            )

        cart_items = db.session.scalars(
            select(CartItem)
            .where(CartItem.cart_id == cart.id)
            .order_by(CartItem.product_id.asc())
        ).all()
        if not cart_items:
            raise ApiError(
                "Keranjang belanja kosong.",
                status_code=422,
                code="cart_empty",
            )

        product_ids = sorted({item.product_id for item in cart_items})
        products = db.session.scalars(
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id.asc())
            .with_for_update()
        ).all()
        product_map = {product.id: product for product in products}

        inventories = db.session.scalars(
            select(Inventory)
            .where(Inventory.product_id.in_(product_ids))
            .order_by(Inventory.product_id.asc())
            .with_for_update()
        ).all()
        inventory_map = {
            inventory.product_id: inventory for inventory in inventories
        }

        unavailable = []
        minimum_errors = []
        stock_errors = []

        for item in cart_items:
            product = product_map.get(item.product_id)
            quantity = int(item.quantity)

            if product is None or product.product_status != "active":
                unavailable.append(
                    {
                        "product_id": item.product_id,
                        "product_name": (
                            product.product_name if product else None
                        ),
                        "product_status": (
                            product.product_status if product else None
                        ),
                        "reason": "Produk tidak aktif atau tidak ditemukan.",
                    }
                )
                continue

            ensure_not_self_purchase(
                buyer=user,
                seller_profile_id=product.business_id,
            )

            if quantity < int(product.minimum_order):
                minimum_errors.append(
                    {
                        "product_id": product.id,
                        "product_name": product.product_name,
                        "quantity": quantity,
                        "minimum_order": int(product.minimum_order),
                    }
                )
                continue

            inventory = inventory_map.get(product.id)
            available = (
                int(inventory.available_quantity)
                if inventory is not None
                else 0
            )
            if inventory is None or available < quantity:
                stock_errors.append(
                    {
                        "product_id": product.id,
                        "product_name": product.product_name,
                        "requested_quantity": quantity,
                        "available_quantity": available,
                    }
                )

        if unavailable:
            _checkout_error(
                "product_unavailable",
                "Salah satu produk di keranjang tidak tersedia.",
                unavailable,
            )
        if minimum_errors:
            _checkout_error(
                "minimum_order_not_met",
                "Jumlah salah satu produk tidak memenuhi minimum order.",
                minimum_errors,
            )
        if stock_errors:
            _checkout_error(
                "insufficient_stock",
                "Stok salah satu produk tidak mencukupi.",
                stock_errors,
            )

        shipping_address = _shipping_address(user, values)
        payment_method = values.get("payment_method")
        payment_reference = values.get("payment_reference")
        buyer_note = values.get("buyer_note")

        groups: dict[int, list[tuple[CartItem, Product, Inventory]]] = {}
        for item in cart_items:
            product = product_map[item.product_id]
            inventory = inventory_map[product.id]
            groups.setdefault(product.business_id, []).append(
                (item, product, inventory)
            )

        order_ids: list[int] = []

        for seller_id in sorted(groups.keys()):
            group_items = groups[seller_id]
            total = Decimal("0.00")
            order = Order(
                order_number=_order_number(),
                buyer_id=user.id,
                seller_id=seller_id,
                total_amount=Decimal("0.00"),
                shipping_address=shipping_address,
                buyer_note=buyer_note,
                order_status="pending",
            )
            db.session.add(order)
            db.session.flush()

            for item, product, inventory in group_items:
                try:
                    price = Decimal(str(product.price)).quantize(
                        Decimal("0.01")
                    )
                    subtotal = (price * int(item.quantity)).quantize(
                        Decimal("0.01")
                    )
                except (InvalidOperation, ValueError, TypeError) as exc:
                    raise ApiError(
                        "Harga produk tidak valid.",
                        status_code=409,
                        code="invalid_product_price",
                        details={"product_id": product.id},
                    ) from exc

                validate_order_total(subtotal)
                total += subtotal

                db.session.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        product_name=product.product_name,
                        price_snapshot=price,
                        quantity=int(item.quantity),
                        subtotal=subtotal,
                    )
                )

                inventory.stock_quantity = (
                    int(inventory.stock_quantity) - int(item.quantity)
                )

            order.total_amount = validate_order_total(total)

            db.session.add(
                Payment(
                    order_id=order.id,
                    payment_method=payment_method,
                    payment_reference=payment_reference,
                    payment_status="unpaid",
                    amount=order.total_amount,
                )
            )
            db.session.add(
                OrderStatusLog(
                    order_id=order.id,
                    changed_by=user.id,
                    old_status=None,
                    new_status="pending",
                    notes="Pesanan dibuat dari checkout keranjang.",
                )
            )
            order_ids.append(order.id)

        for item in cart_items:
            db.session.delete(item)
        cart.status = "converted"

        db.session.commit()

        orders = db.session.scalars(
            select(Order)
            .where(Order.id.in_(order_ids))
            .order_by(Order.id.asc())
            .options(*_order_options(include_logs=True))
        ).all()

        # Notifikasi pesanan baru untuk setiap penjual terkait.
        for order in orders:
            create_notification(
                user_id=_profile_user_id(order.seller_id),
                title="Pesanan baru masuk",
                message=(
                    f"Pesanan baru #{order.order_number} dengan total "
                    f"Rp{order.total_amount:,.0f} menunggu konfirmasi Anda."
                ).replace(",", "."),
                type_="order",
                link="/seller/pesanan/" + str(order.id),
                dedupe_key=f"order_new:{order.id}",
            )
        # Hook notifikasi dijalankan setelah commit utama; commit agar
        # notifikasi tidak hilang saat request selesai.
        db.session.commit()

        return [
            serialize_order(order, "buyer", include_logs=True)
            for order in orders
        ]
    except ApiError:
        db.session.rollback()
        raise
    except IntegrityError as exc:
        db.session.rollback()
        raise ApiError(
            "Checkout gagal karena konflik data. Silakan coba lagi.",
            status_code=409,
            code="checkout_conflict",
        ) from exc
    except Exception:
        db.session.rollback()
        raise


def _restore_order_stock(order: Order) -> None:
    items = list(order.items)
    if not items:
        return

    product_ids = sorted({item.product_id for item in items})
    inventories = db.session.scalars(
        select(Inventory)
        .where(Inventory.product_id.in_(product_ids))
        .order_by(Inventory.product_id.asc())
        .with_for_update()
    ).all()
    inventory_map = {
        inventory.product_id: inventory for inventory in inventories
    }

    for item in items:
        inventory = inventory_map.get(item.product_id)
        if inventory is None:
            inventory = Inventory(
                product_id=item.product_id,
                stock_quantity=0,
                reserved_quantity=0,
            )
            db.session.add(inventory)
            db.session.flush()
            inventory_map[item.product_id] = inventory

        new_stock = int(inventory.stock_quantity) + int(item.quantity)
        if new_stock > MAX_UNSIGNED_INT:
            raise ApiError(
                "Stok melebihi batas maksimum saat pengembalian.",
                status_code=422,
                code="stock_overflow",
                details={"product_id": item.product_id},
            )
        inventory.stock_quantity = new_stock


def cancel_order(user, order_id: int, data: dict) -> dict:
    values = validate_cancel_payload(data)

    try:
        order = _get_buyer_order(user, order_id, for_update=True)
        if order.order_status not in BUYER_CANCELLABLE_STATUSES:
            raise ApiError(
                "Pesanan tidak dapat dibatalkan pada status ini.",
                status_code=409,
                code="order_cannot_be_cancelled",
                details={
                    "order_status": order.order_status,
                    "cancellable_statuses": sorted(
                        BUYER_CANCELLABLE_STATUSES
                    ),
                },
            )

        old_status = order.order_status
        _restore_order_stock(order)
        order.order_status = "cancelled"

        notes = (
            values.get("reason")
            or values.get("notes")
            or "Pesanan dibatalkan oleh pembeli."
        )
        db.session.add(
            OrderStatusLog(
                order_id=order.id,
                changed_by=user.id,
                old_status=old_status,
                new_status="cancelled",
                notes=notes,
            )
        )

        db.session.commit()
        order = _reload_order(order.id, include_logs=True)

        # Notifikasi pembatalan untuk penjual.
        create_notification(
            user_id=_profile_user_id(order.seller_id),
            title="Pesanan dibatalkan pembeli",
            message=(
                f"Pesanan #{order.order_number} dibatalkan pembeli: {notes}"
            ),
            type_="order",
            link="/seller/pesanan/" + str(order.id),
            dedupe_key=f"order:{order.id}:cancelled",
        )
        db.session.commit()

        return serialize_order(order, "buyer", include_logs=True)
    except ApiError:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        raise


def update_order_status(user, order_id: int, data: dict) -> dict:
    values = validate_order_status_payload(data)
    target_status = values["status"]

    try:
        order = _get_seller_order(user, order_id, for_update=True)
        current_status = order.order_status

        if target_status == current_status:
            raise ApiError(
                "Status pesanan tidak berubah.",
                status_code=409,
                code="order_status_unchanged",
                details={"order_status": current_status},
            )

        allowed = SELLER_STATUS_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            raise ApiError(
                "Perubahan status pesanan tidak diizinkan.",
                status_code=409,
                code="invalid_status_transition",
                details={
                    "current_status": current_status,
                    "requested_status": target_status,
                    "allowed_statuses": allowed,
                },
            )

        if target_status == "processing":
            # Impor tertunda: payment_service mengimpor fungsi dari modul ini.
            from services.payment_service import _latest_payment

            payment = _latest_payment(order.id, for_update=True)
            if payment is None or payment.payment_status != "paid":
                raise ApiError(
                    "Pembayaran belum dikonfirmasi; pesanan tidak dapat "
                    "diproses.",
                    status_code=409,
                    code="payment_not_paid",
                    details={
                        "payment_status": (
                            payment.payment_status if payment else "unpaid"
                        ),
                        "required_status": "paid",
                    },
                )

        if target_status == "cancelled":
            _restore_order_stock(order)

        order.order_status = target_status
        notes = values.get("notes") or (
            f"Status pesanan diubah dari {current_status} "
            f"menjadi {target_status}."
        )
        db.session.add(
            OrderStatusLog(
                order_id=order.id,
                changed_by=user.id,
                old_status=current_status,
                new_status=target_status,
                notes=notes,
            )
        )

        db.session.commit()
        order = _reload_order(order.id, include_logs=True)

        # Notifikasi perubahan status untuk pembeli.
        _notify_status_change(order, current_status, target_status)
        db.session.commit()

        return serialize_order(order, "seller", include_logs=True)
    except ApiError:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        raise


def receive_order(user, order_id: int) -> dict:
    """Buyer menandai barang diterima: shipped → completed."""
    try:
        order = _get_buyer_order(user, order_id, for_update=True)
        current_status = order.order_status
        if current_status != "shipped":
            raise ApiError(
                "Konfirmasi penerimaan hanya dapat dilakukan pada pesanan "
                "yang sudah dikirim.",
                status_code=409,
                code="order_receive_not_allowed",
                details={"order_status": current_status},
            )

        target_status = "completed"
        order.order_status = target_status
        db.session.add(
            OrderStatusLog(
                order_id=order.id,
                changed_by=user.id,
                old_status=current_status,
                new_status=target_status,
                notes="Barang diterima oleh pembeli.",
            )
        )

        db.session.commit()
        order = _reload_order(order.id, include_logs=True)

        # Notifikasi penyelesaian untuk penjual.
        create_notification(
            user_id=_profile_user_id(order.seller_id),
            title="Pesanan selesai",
            message=(
                f"Pesanan #{order.order_number} telah dikonfirmasi diterima "
                "oleh pembeli."
            ),
            type_="order",
            link="/seller/pesanan/" + str(order.id),
            dedupe_key=f"order:{order.id}:completed",
        )
        db.session.commit()

        return serialize_order(order, "buyer", include_logs=True)
    except ApiError:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        raise


_STATUS_MESSAGES = {
    "confirmed": "kini diproses penjual.",
    "processing": "sedang kami proses.",
    "shipped": "selesai dikirim; mohon konfirmasi penerimaan.",
    "cancelled": "dibatalkan penjual.",
    "completed": "telah diselesaikan penjual.",
}


def _notify_status_change(order, old_status: str, new_status: str) -> None:
    if new_status not in _STATUS_MESSAGES:
        return
    titles = {
        "confirmed": "Pesanan dikonfirmasi",
        "processing": "Pesanan diproses",
        "shipped": "Pesanan dikirim",
        "cancelled": "Pesanan dibatalkan",
        "completed": "Pesanan selesai",
    }
    create_notification(
        user_id=order.buyer_id,
        title=titles.get(new_status, "Status pesanan berubah"),
        message=f"Pesanan #{order.order_number} {_STATUS_MESSAGES[new_status]}",
        type_="order",
        link="/pesanan/" + str(order.id),
        dedupe_key=f"order:{order.id}:{new_status}",
    )
