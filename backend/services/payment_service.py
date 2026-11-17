"""Logika pencatatan dan konfirmasi pembayaran di luar aplikasi."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select

from extensions import db
from models import BusinessProfile, Payment
from services.notification_service import create_notification
from services.order_service import (
    _get_buyer_order,
    _get_seller_order,
    serialize_payment,
)
from services.payment_proof_storage_service import (
    delete_payment_proof,
    payment_proof_mimetype,
    resolve_payment_proof,
    save_payment_proof,
    safe_payment_proof_download_name,
)
from utils.api_error import ApiError
from utils.order_validators import (
    BUYER_PAYMENT_SUBMITTABLE_STATUSES,
    ensure_not_self_purchase,
    validate_payment_confirm_payload,
    validate_payment_submit_payload,
)


def _latest_payment(order_id: int, *, for_update: bool = False):
    stmt = (
        select(Payment)
        .where(Payment.order_id == order_id)
        .order_by(Payment.id.desc())
        .limit(1)
    )
    if for_update:
        # populate_existing memaksa instance di identity map menyegarkan
        # dirinya dari baris hasil baca terkunci, sehingga validasi tidak
        # pernah membaca nilai lama yang sudah kedaluwarsa di memori.
        stmt = stmt.with_for_update().execution_options(
            populate_existing=True
        )
    return db.session.scalar(stmt)


def _ensure_payment(order):
    payment = _latest_payment(order.id, for_update=True)
    if payment is not None:
        return payment

    payment = Payment(
        order_id=order.id,
        payment_method=None,
        payment_reference=None,
        payment_status="unpaid",
        amount=Decimal(order.total_amount).quantize(Decimal("0.01")),
    )
    db.session.add(payment)
    db.session.flush()
    return payment


def _amount(order) -> Decimal:
    try:
        return Decimal(str(order.total_amount)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ApiError(
            "Total pesanan tidak valid.",
            status_code=409,
            code="invalid_order_total",
        ) from exc


def get_buyer_payment(user, order_id: int) -> dict:
    order = _get_buyer_order(user, order_id, include_logs=False)
    payments = list(order.payments)
    payment = payments[-1] if payments else None
    return {
        "order_id": order.id,
        "order_status": order.order_status,
        "payment": serialize_payment(payment),
    }


def submit_payment(user, order_id: int, data: dict) -> dict:
    values = validate_payment_submit_payload(data)

    try:
        order = _get_buyer_order(user, order_id, for_update=True)
        if order.order_status not in BUYER_PAYMENT_SUBMITTABLE_STATUSES:
            raise ApiError(
                "Pembayaran hanya dapat diajukan pada status pesanan "
                "tertentu.",
                status_code=409,
                code="payment_order_status_not_allowed",
                details={
                    "order_status": order.order_status,
                    "allowed_statuses": sorted(
                        BUYER_PAYMENT_SUBMITTABLE_STATUSES
                    ),
                },
            )

        payment = _ensure_payment(order)
        if payment.payment_status != "unpaid":
            raise ApiError(
                "Pembayaran belum dapat diajukan pada status ini.",
                status_code=409,
                code="payment_not_pending_submission",
                details={
                    "status": payment.payment_status,
                    "allowed_status": "unpaid",
                },
            )

        method = values.get("payment_method", payment.payment_method)
        if not method:
            raise ApiError(
                "Metode pembayaran wajib diisi.",
                status_code=422,
                errors={
                    "payment_method": "Isi metode pembayaran yang digunakan."
                },
                code="payment_method_required",
            )

        payment.payment_method = method
        if "payment_reference" in values:
            payment.payment_reference = values["payment_reference"]
        payment.paid_at = values.get("paid_at") or datetime.now()
        payment.amount = _amount(order)
        payment.payment_status = "pending_confirmation"

        db.session.commit()

        # Notifikasi ke penjual: pembayaran menunggu konfirmasi.
        seller_user_id = db.session.scalar(
            select(BusinessProfile.user_id).where(
                BusinessProfile.id == order.seller_id
            )
        )
        create_notification(
            user_id=seller_user_id,
            title="Pembayaran menunggu konfirmasi",
            message=(
                "Pembeli mengajukan pembayaran untuk pesanan "
                f"#{order.order_number}. Harap konfirmasi pembayaran."
            ),
            type_="payment",
            link="/seller/pesanan/" + str(order.id),
            dedupe_key=f"payment_submitted:{order.id}:{payment.id}",
        )
        db.session.commit()

        payment = _latest_payment(order.id)
        return {
            "order_id": order.id,
            "order_status": order.order_status,
            "payment": serialize_payment(payment),
        }
    except ApiError:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        raise


def confirm_payment(user, order_id: int, data: dict) -> dict:
    values = validate_payment_confirm_payload(data)

    try:
        order = _get_seller_order(user, order_id, for_update=True)
        ensure_not_self_purchase(
            buyer_user_id=order.buyer_id,
            seller_user_id=user.id,
            message=(
                "Anda tidak dapat mengonfirmasi pembayaran untuk pesanan "
                "yang Anda beli sendiri."
            ),
        )
        if order.order_status == "cancelled":
            raise ApiError(
                "Pesanan sudah dibatalkan; pembayaran tidak dapat dikonfirmasi.",
                status_code=409,
                code="order_cancelled",
            )
        if order.order_status == "completed":
            raise ApiError(
                "Pesanan sudah selesai; pembayaran tidak dapat dikonfirmasi.",
                status_code=409,
                code="order_completed",
            )

        payment = _ensure_payment(order)
        if payment.payment_status == "paid":
            raise ApiError(
                "Pembayaran sudah dikonfirmasi.",
                status_code=409,
                code="payment_already_paid",
            )
        if payment.payment_status == "refunded":
            raise ApiError(
                "Pembayaran sudah direfund.",
                status_code=409,
                code="payment_already_refunded",
            )
        if payment.payment_status != "pending_confirmation":
            raise ApiError(
                "Pembayaran belum diajukan oleh pembeli.",
                status_code=409,
                code="payment_not_pending_confirmation",
                details={
                    "status": payment.payment_status,
                    "allowed_status": "pending_confirmation",
                },
            )

        method = values.get("payment_method", payment.payment_method)
        if not method:
            raise ApiError(
                "Metode pembayaran wajib diisi.",
                status_code=422,
                errors={
                    "payment_method": "Isi metode pembayaran yang diterima."
                },
                code="payment_method_required",
            )

        expected_amount = _amount(order)
        try:
            actual_amount = Decimal(str(payment.amount)).quantize(
                Decimal("0.01")
            )
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ApiError(
                "Nominal pembayaran tidak valid.",
                status_code=409,
                code="payment_amount_mismatch",
            ) from exc

        if actual_amount != expected_amount:
            raise ApiError(
                "Nominal pembayaran tidak sesuai total pesanan.",
                status_code=409,
                code="payment_amount_mismatch",
                details={
                    "payment_amount": float(actual_amount),
                    "order_total": float(expected_amount),
                },
            )

        payment.payment_method = method
        if "payment_reference" in values:
            payment.payment_reference = values["payment_reference"]
        payment.amount = expected_amount
        payment.paid_at = values.get("paid_at") or payment.paid_at or datetime.now()
        payment.payment_status = "paid"

        db.session.commit()

        # Notifikasi ke pembeli: pembayaran telah dikonfirmasi penjual.
        create_notification(
            user_id=order.buyer_id,
            title="Pembayaran dikonfirmasi",
            message=(
                f"Pembayaran pesanan #{order.order_number} telah dikonfirmasi "
                "oleh penjual."
            ),
            type_="payment",
            link="/pesanan/" + str(order.id),
            dedupe_key=f"payment_confirmed:{order.id}:{payment.id}",
        )
        db.session.commit()

        payment = _latest_payment(order.id)
        return {
            "order_id": order.id,
            "order_status": order.order_status,
            "payment": serialize_payment(payment),
        }
    except ApiError:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        raise


def _payment_proof_payload(payment: Payment) -> dict | None:
    if not payment.proof_file_path:
        return None

    return {
        "file_name": Path(payment.proof_file_path).name,
        "mime_type": payment_proof_mimetype(payment.proof_file_path),
        "download_url": (
            f"/api/orders/{int(payment.order_id)}/payment/proof/download"
        ),
    }


def upload_payment_proof(user, order_id: int, file_storage) -> dict:
    try:
        order = _get_buyer_order(user, order_id, for_update=True, include_logs=False)
        if order.order_status == "cancelled":
            raise ApiError(
                "Pesanan sudah dibatalkan; bukti pembayaran tidak dapat diunggah.",
                status_code=409,
                code="order_cancelled",
            )
        if order.order_status == "completed":
            raise ApiError(
                "Pesanan sudah selesai; bukti pembayaran tidak dapat diunggah.",
                status_code=409,
                code="order_completed",
            )

        payment = _latest_payment(order.id, for_update=True)
        if payment is None:
            payment = _ensure_payment(order)
        if payment.payment_status != "pending_confirmation":
            raise ApiError(
                "Bukti pembayaran hanya dapat diunggah saat pembayaran "
                "menunggu konfirmasi.",
                status_code=409,
                code="payment_proof_not_pending_confirmation",
                details={
                    "status": payment.payment_status,
                    "allowed_status": "pending_confirmation",
                },
            )

        relative_path = save_payment_proof(file_storage, order.id)
        previous_path = payment.proof_file_path
        payment.proof_file_path = relative_path

        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            delete_payment_proof(relative_path)
            raise ApiError(
                "Bukti pembayaran gagal disimpan.",
                status_code=500,
                code="payment_proof_save_failed",
            ) from exc

        if previous_path and previous_path != relative_path:
            delete_payment_proof(previous_path)

        db.session.refresh(payment)
        return {
            "order_id": order.id,
            "order_status": order.order_status,
            "payment": serialize_payment(payment),
            "proof": _payment_proof_payload(payment),
        }
    except ApiError:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        raise


def get_buyer_payment_proof(user, order_id: int):
    order = _get_buyer_order(user, order_id, include_logs=False)
    payment = _latest_payment(order.id)
    if payment is None or not payment.proof_file_path:
        raise ApiError(
            "Bukti pembayaran tidak ditemukan.",
            status_code=404,
            code="payment_proof_not_found",
        )

    path = resolve_payment_proof(payment.proof_file_path)
    return (
        path,
        safe_payment_proof_download_name(order.id, payment.proof_file_path),
        payment_proof_mimetype(payment.proof_file_path),
    )


def get_seller_payment_proof(user, order_id: int):
    order = _get_seller_order(user, order_id, include_logs=False)
    payment = _latest_payment(order.id)
    if payment is None or not payment.proof_file_path:
        raise ApiError(
            "Bukti pembayaran tidak ditemukan.",
            status_code=404,
            code="payment_proof_not_found",
        )

    path = resolve_payment_proof(payment.proof_file_path)
    return (
        path,
        safe_payment_proof_download_name(order.id, payment.proof_file_path),
        payment_proof_mimetype(payment.proof_file_path),
    )
