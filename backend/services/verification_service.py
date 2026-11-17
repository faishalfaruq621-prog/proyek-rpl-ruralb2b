"""Logika pengajuan, dokumen, dan keputusan verifikasi UMKM."""

from datetime import datetime

from flask import current_app
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload

from extensions import db
from models import (
    BusinessProfile,
    VerificationDocument,
    VerificationLog,
    VerificationRequest,
)
from services.notification_service import create_notification
from services.storage_service import (
    delete_stored_file,
    mimetype_for_path,
    resolve_stored_file,
    safe_download_name,
    save_document,
)
from services.telegram_service import (
    notify_admin_new_verification,
    notify_admin_verification_approved,
    notify_admin_verification_rejected,
)
from utils.api_error import ApiError
from utils.validators import DOCUMENT_TYPES

VERIFICATION_STATUSES = {"pending", "approved", "rejected"}
_MAX_NOTES_LENGTH = 2000


def _get_profile(user, lock: bool = False) -> BusinessProfile:
    statement = db.select(BusinessProfile).where(
        BusinessProfile.user_id == user.id
    )
    if lock:
        statement = statement.with_for_update()
    profile = db.session.scalar(statement)
    if profile is None:
        raise ApiError(
            "Profil bisnis belum tersedia untuk akun ini.",
            status_code=404,
            code="business_profile_not_found",
        )
    return profile


def _document_payload(document: VerificationDocument, audience: str) -> dict:
    data = document.to_dict()
    prefix = (
        "/api/admin/verifications"
        if audience == "admin"
        else "/api/business/verifications"
    )
    data["download_url"] = (
        f"{prefix}/{document.verification_id}/documents/{document.id}/download"
    )
    return data


def _verification_payload(request_obj: VerificationRequest, audience: str) -> dict:
    is_admin = audience == "admin"
    verification = request_obj.to_dict(
        include_profile=True,
        include_reviewer=is_admin,
    )
    payload = {
        "verification": verification,
        "documents": [
            _document_payload(document, audience)
            for document in request_obj.documents
        ],
        "history": [
            log.to_dict(include_admin=is_admin) for log in request_obj.logs
        ],
    }
    if is_admin:
        payload["telegram_notifications"] = [
            log.to_dict() for log in request_obj.telegram_logs
        ]
    return payload


def _optional_note(value, field: str = "notes") -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={field: "Catatan harus berupa teks."},
        )
    value = value.strip()
    if not value:
        return None
    if len(value) > _MAX_NOTES_LENGTH:
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={field: f"Catatan maksimal {_MAX_NOTES_LENGTH} karakter."},
        )
    return value


def _required_reason(value) -> str:
    if not isinstance(value, str):
        raise ApiError(
            "Alasan penolakan wajib diisi.",
            status_code=422,
            errors={"rejection_reason": "Alasan penolakan wajib diisi."},
            code="rejection_reason_required",
        )
    value = value.strip()
    if not value:
        raise ApiError(
            "Alasan penolakan wajib diisi.",
            status_code=422,
            errors={"rejection_reason": "Alasan penolakan wajib diisi."},
            code="rejection_reason_required",
        )
    if len(value) > _MAX_NOTES_LENGTH:
        raise ApiError(
            "Alasan penolakan terlalu panjang.",
            status_code=422,
            errors={
                "rejection_reason": (
                    f"Alasan penolakan maksimal {_MAX_NOTES_LENGTH} karakter."
                )
            },
        )
    return value


def _lock_verification(verification_id: int, profile_id: int | None = None):
    statement = db.select(VerificationRequest).where(
        VerificationRequest.id == verification_id
    )
    if profile_id is not None:
        statement = statement.where(
            VerificationRequest.business_profile_id == profile_id
        )
    request_obj = db.session.execute(
        statement.with_for_update()
    ).scalar_one_or_none()
    if request_obj is None:
        raise ApiError(
            "Pengajuan verifikasi tidak ditemukan.",
            status_code=404,
            code="verification_not_found",
        )
    return request_obj


def list_user_verifications(user, page: int, per_page: int) -> tuple[list, object]:
    profile = _get_profile(user)
    statement = (
        db.select(VerificationRequest)
        .where(VerificationRequest.business_profile_id == profile.id)
        .options(selectinload(VerificationRequest.documents))
        .order_by(
            VerificationRequest.submitted_at.desc(),
            VerificationRequest.id.desc(),
        )
    )
    pagination = db.paginate(
        statement, page=page, per_page=per_page, error_out=False
    )
    items = [
        request_obj.to_dict(include_documents_count=True)
        for request_obj in pagination.items
    ]
    return items, pagination


def get_user_verification(user, verification_id: int) -> dict:
    profile = _get_profile(user)
    statement = (
        db.select(VerificationRequest)
        .where(
            VerificationRequest.id == verification_id,
            VerificationRequest.business_profile_id == profile.id,
        )
        .options(
            selectinload(VerificationRequest.documents),
            selectinload(VerificationRequest.logs),
        )
    )
    request_obj = db.session.scalar(statement)
    if request_obj is None:
        raise ApiError(
            "Pengajuan verifikasi tidak ditemukan.",
            status_code=404,
            code="verification_not_found",
        )
    return _verification_payload(request_obj, audience="business")


def create_verification(user) -> tuple[dict, dict]:
    # Lock baris profil agar dua request bersamaan tidak membuat dua pengajuan
    # pending sekaligus untuk profil yang sama.
    profile = _get_profile(user, lock=True)

    pending = db.session.scalar(
        db.select(VerificationRequest)
        .where(
            VerificationRequest.business_profile_id == profile.id,
            VerificationRequest.status == "pending",
        )
        .limit(1)
    )
    if pending is not None:
        raise ApiError(
            "Masih ada pengajuan verifikasi yang sedang diproses.",
            status_code=409,
            code="verification_already_pending",
            details={"verification_id": pending.id},
        )

    request_obj = VerificationRequest(
        business_profile_id=profile.id,
        status="pending",
    )
    log = VerificationLog(
        verification=request_obj,
        admin_id=None,
        old_status=None,
        new_status="pending",
        notes="Pengajuan verifikasi dibuat.",
    )

    db.session.add(request_obj)
    db.session.add(log)

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(
            "Gagal membuat pengajuan verifikasi", exc_info=current_app.debug
        )
        raise ApiError(
            "Pengajuan verifikasi gagal disimpan.",
            status_code=500,
            code="verification_create_failed",
        ) from exc

    verification_id = request_obj.id

    try:
        notification = notify_admin_new_verification(request_obj)
    except Exception:
        db.session.rollback()
        current_app.logger.error(
            "Notifikasi Telegram gagal tanpa membatalkan pengajuan",
            exc_info=current_app.debug,
        )
        notification = {"sent": False, "reason": "delivery_failed"}

    # Ambil ulang setelah commit notifikasi karena objek ORM bisa expired.
    request_obj = db.session.scalar(
        db.select(VerificationRequest)
        .where(VerificationRequest.id == verification_id)
        .options(
            selectinload(VerificationRequest.documents),
            selectinload(VerificationRequest.logs),
        )
    )

    return _verification_payload(request_obj, audience="business"), notification


def upload_document(user, verification_id: int, document_type, file_storage) -> dict:
    profile = _get_profile(user)
    request_obj = _lock_verification(verification_id, profile_id=profile.id)

    if request_obj.status != "pending":
        raise ApiError(
            "Dokumen hanya dapat diunggah pada pengajuan yang masih pending.",
            status_code=409,
            code="verification_not_pending",
            details={"status": request_obj.status},
        )

    if not isinstance(document_type, str) or not document_type.strip():
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={"document_type": "Jenis dokumen wajib diisi."},
        )

    document_type = document_type.strip().lower()
    if document_type not in DOCUMENT_TYPES:
        raise ApiError(
            "Jenis dokumen tidak valid.",
            status_code=422,
            errors={
                "document_type": (
                    "Pilihan: " + ", ".join(sorted(DOCUMENT_TYPES)) + "."
                )
            },
        )

    document_count = db.session.scalar(
        db.select(func.count())
        .select_from(VerificationDocument)
        .where(VerificationDocument.verification_id == request_obj.id)
    )
    max_documents = int(current_app.config["MAX_VERIFICATION_DOCUMENTS"])
    if document_count >= max_documents:
        raise ApiError(
            "Jumlah dokumen sudah mencapai batas.",
            status_code=409,
            code="document_limit_reached",
            details={"max_documents": max_documents},
        )

    # Validasi dan simpan file. Jika commit database gagal, file dihapus.
    relative_path = save_document(file_storage, profile.id, request_obj.id)

    document = VerificationDocument(
        verification_id=request_obj.id,
        document_type=document_type,
        file_path=relative_path,
    )
    db.session.add(document)

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        delete_stored_file(relative_path)
        current_app.logger.error(
            "Gagal menyimpan metadata dokumen verifikasi",
            exc_info=current_app.debug,
        )
        raise ApiError(
            "Dokumen gagal disimpan.",
            status_code=500,
            code="document_save_failed",
        ) from exc

    db.session.refresh(document)
    return _document_payload(document, audience="business")


def admin_list_verifications(
    status: str | None, page: int, per_page: int
) -> tuple[list, object]:
    if status is not None and status not in VERIFICATION_STATUSES:
        raise ApiError(
            "Filter status tidak valid.",
            status_code=422,
            errors={
                "status": "Pilihan: pending, approved, rejected."
            },
        )

    statement = (
        db.select(VerificationRequest)
        .options(
            joinedload(VerificationRequest.business_profile).joinedload(
                BusinessProfile.user
            ),
            selectinload(VerificationRequest.documents),
        )
        .order_by(
            VerificationRequest.submitted_at.desc(),
            VerificationRequest.id.desc(),
        )
    )
    if status is not None:
        statement = statement.where(VerificationRequest.status == status)

    pagination = db.paginate(
        statement, page=page, per_page=per_page, error_out=False
    )
    items = [
        request_obj.to_dict(
            include_profile=True,
            include_documents_count=True,
        )
        for request_obj in pagination.items
    ]
    return items, pagination


def get_admin_verification(verification_id: int) -> dict:
    statement = (
        db.select(VerificationRequest)
        .where(VerificationRequest.id == verification_id)
        .options(
            joinedload(VerificationRequest.business_profile).joinedload(
                BusinessProfile.user
            ),
            joinedload(VerificationRequest.reviewer),
            selectinload(VerificationRequest.documents),
            selectinload(VerificationRequest.logs).joinedload(
                VerificationLog.admin
            ),
            selectinload(VerificationRequest.telegram_logs),
        )
    )
    request_obj = db.session.scalar(statement)
    if request_obj is None:
        raise ApiError(
            "Pengajuan verifikasi tidak ditemukan.",
            status_code=404,
            code="verification_not_found",
        )
    return _verification_payload(request_obj, audience="admin")


def admin_approve(user, verification_id: int, data: dict) -> dict:
    notes = _optional_note(data.get("notes"))
    request_obj = _lock_verification(verification_id)

    if request_obj.status != "pending":
        raise ApiError(
            "Pengajuan ini sudah diproses.",
            status_code=409,
            code="verification_not_pending",
            details={"status": request_obj.status},
        )

    document_count = db.session.scalar(
        db.select(func.count())
        .select_from(VerificationDocument)
        .where(VerificationDocument.verification_id == request_obj.id)
    )
    if document_count == 0:
        raise ApiError(
            "Pengajuan belum memiliki dokumen pendukung.",
            status_code=422,
            code="documents_required",
        )

    old_status = request_obj.status
    request_obj.status = "approved"
    request_obj.reviewed_by = user.id
    request_obj.reviewed_at = datetime.now()
    request_obj.rejection_reason = None

    log = VerificationLog(
        verification_id=request_obj.id,
        admin_id=user.id,
        old_status=old_status,
        new_status="approved",
        notes=notes or "Pengajuan verifikasi disetujui.",
    )
    db.session.add(log)

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(
            "Gagal menyetujui verifikasi", exc_info=current_app.debug
        )
        raise ApiError(
            "Keputusan verifikasi gagal disimpan.",
            status_code=500,
            code="verification_review_failed",
        ) from exc

    # Notifikasi in-app untuk pemilik bisnis (non-fatal).
    try:
        owner_user_id = db.session.scalar(
            db.select(BusinessProfile.user_id).where(
                BusinessProfile.id == request_obj.business_profile_id
            )
        )
        if owner_user_id is not None:
            create_notification(
                user_id=owner_user_id,
                title="Verifikasi bisnis disetujui",
                message=(
                    "Pengajuan verifikasi bisnis Anda telah disetujui "
                    "administrator."
                ),
                type_="verification",
                link="/verifikasi",
                dedupe_key=f"verification:{request_obj.id}:approved",
            )
            db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.error(
            "Notifikasi verifikasi disetujui gagal non-fatal",
            exc_info=current_app.debug,
        )

    # Notifikasi Telegram untuk admin (non-fatal; kegagalan tidak
    # memengaruhi keputusan yang sudah tersimpan).
    try:
        telegram = notify_admin_verification_approved(request_obj)
    except Exception:
        db.session.rollback()
        telegram = {"sent": False, "reason": "delivery_failed"}
        current_app.logger.error(
            "Notifikasi Telegram (disetujui) gagal non-fatal",
            exc_info=current_app.debug,
        )

    return get_admin_verification(verification_id), telegram


def admin_reject(user, verification_id: int, data: dict) -> dict:
    reason = _required_reason(data.get("rejection_reason"))
    notes = _optional_note(data.get("notes"))
    request_obj = _lock_verification(verification_id)

    if request_obj.status != "pending":
        raise ApiError(
            "Pengajuan ini sudah diproses.",
            status_code=409,
            code="verification_not_pending",
            details={"status": request_obj.status},
        )

    old_status = request_obj.status
    request_obj.status = "rejected"
    request_obj.reviewed_by = user.id
    request_obj.reviewed_at = datetime.now()
    request_obj.rejection_reason = reason

    log = VerificationLog(
        verification_id=request_obj.id,
        admin_id=user.id,
        old_status=old_status,
        new_status="rejected",
        notes=notes or f"Pengajuan ditolak: {reason}",
    )
    db.session.add(log)

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(
            "Gagal menolak verifikasi", exc_info=current_app.debug
        )
        raise ApiError(
            "Keputusan verifikasi gagal disimpan.",
            status_code=500,
            code="verification_review_failed",
        ) from exc

    # Notifikasi in-app untuk pemilik bisnis (non-fatal).
    try:
        owner_user_id = db.session.scalar(
            db.select(BusinessProfile.user_id).where(
                BusinessProfile.id == request_obj.business_profile_id
            )
        )
        if owner_user_id is not None:
            create_notification(
                user_id=owner_user_id,
                title="Verifikasi bisnis ditolak",
                message=(
                    f"Pengajuan verifikasi bisnis Anda ditolak: {reason}"
                ),
                type_="verification",
                link="/verifikasi",
                dedupe_key=f"verification:{request_obj.id}:rejected",
            )
            db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.error(
            "Notifikasi verifikasi ditolak gagal non-fatal",
            exc_info=current_app.debug,
        )

    # Notifikasi Telegram untuk admin (non-fatal).
    try:
        telegram = notify_admin_verification_rejected(request_obj)
    except Exception:
        db.session.rollback()
        telegram = {"sent": False, "reason": "delivery_failed"}
        current_app.logger.error(
            "Notifikasi Telegram (ditolak) gagal non-fatal",
            exc_info=current_app.debug,
        )

    return get_admin_verification(verification_id), telegram


def admin_logs(verification_id: int) -> list:
    exists = db.session.scalar(
        db.select(VerificationRequest.id).where(
            VerificationRequest.id == verification_id
        )
    )
    if exists is None:
        raise ApiError(
            "Pengajuan verifikasi tidak ditemukan.",
            status_code=404,
            code="verification_not_found",
        )

    statement = (
        db.select(VerificationLog)
        .where(VerificationLog.verification_id == verification_id)
        .options(joinedload(VerificationLog.admin))
        .order_by(VerificationLog.created_at.asc(), VerificationLog.id.asc())
    )
    logs = db.session.scalars(statement).all()
    return [log.to_dict(include_admin=True) for log in logs]


def _document_for_user(user, verification_id: int, document_id: int):
    profile = _get_profile(user)
    statement = (
        db.select(VerificationDocument)
        .join(
            VerificationRequest,
            VerificationDocument.verification_id == VerificationRequest.id,
        )
        .where(
            VerificationDocument.id == document_id,
            VerificationRequest.id == verification_id,
            VerificationRequest.business_profile_id == profile.id,
        )
    )
    document = db.session.scalar(statement)
    if document is None:
        raise ApiError(
            "Dokumen tidak ditemukan.",
            status_code=404,
            code="document_not_found",
        )
    return document


def _document_for_admin(verification_id: int, document_id: int):
    document = db.session.scalar(
        db.select(VerificationDocument).where(
            VerificationDocument.id == document_id,
            VerificationDocument.verification_id == verification_id,
        )
    )
    if document is None:
        raise ApiError(
            "Dokumen tidak ditemukan.",
            status_code=404,
            code="document_not_found",
        )
    return document


def _file_payload(document: VerificationDocument):
    path = resolve_stored_file(document.file_path)
    return (
        path,
        safe_download_name(
            document.document_type, document.id, document.file_path
        ),
        mimetype_for_path(document.file_path),
    )


def get_document_file_for_user(user, verification_id: int, document_id: int):
    document = _document_for_user(user, verification_id, document_id)
    return _file_payload(document)


def get_document_file_for_admin(verification_id: int, document_id: int):
    document = _document_for_admin(verification_id, document_id)
    return _file_payload(document)
