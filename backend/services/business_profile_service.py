"""Logika profil bisnis dan ringkasan status verifikasi."""

from extensions import db
from models import BusinessProfile, VerificationRequest
from utils.api_error import ApiError
from utils.profile_validators import validate_business_profile_payload


def get_profile_for_user(user) -> BusinessProfile:
    profile = db.session.scalar(
        db.select(BusinessProfile).where(BusinessProfile.user_id == user.id)
    )
    if profile is None:
        raise ApiError(
            "Profil bisnis belum tersedia untuk akun ini.",
            status_code=404,
            code="business_profile_not_found",
        )
    return profile


def get_verification_summary(profile: BusinessProfile) -> dict:
    latest = db.session.scalar(
        db.select(VerificationRequest)
        .where(VerificationRequest.business_profile_id == profile.id)
        .order_by(
            VerificationRequest.submitted_at.desc(),
            VerificationRequest.id.desc(),
        )
        .limit(1)
    )
    approved_id = db.session.scalar(
        db.select(VerificationRequest.id)
        .where(
            VerificationRequest.business_profile_id == profile.id,
            VerificationRequest.status == "approved",
        )
        .limit(1)
    )
    pending_id = db.session.scalar(
        db.select(VerificationRequest.id)
        .where(
            VerificationRequest.business_profile_id == profile.id,
            VerificationRequest.status == "pending",
        )
        .limit(1)
    )

    return {
        "status": latest.status if latest else None,
        "is_verified": approved_id is not None,
        "latest_request_id": latest.id if latest else None,
        "pending_request_id": pending_id,
        "rejection_reason": (
            latest.rejection_reason
            if latest is not None and latest.status == "rejected"
            else None
        ),
    }


def build_profile_payload(user) -> dict:
    profile = get_profile_for_user(user)
    return {
        "profile": profile.to_dict(),
        "verification": get_verification_summary(profile),
    }


def update_profile(user, data: dict, partial: bool = False) -> dict:
    profile = get_profile_for_user(user)
    values = validate_business_profile_payload(data, partial=partial)

    # Kemampuan akun: minimal salah satu harus tetap aktif. Nilai efektif
    # memperhitungkan profil eksisting untuk field yang tidak dikirim.
    if "can_buy" in values or "can_sell" in values:
        effective_buy = values.get("can_buy", bool(profile.can_buy))
        effective_sell = values.get("can_sell", bool(profile.can_sell))
        if not (effective_buy or effective_sell):
            raise ApiError(
                "Validasi gagal.",
                status_code=422,
                errors={
                    "can_buy": "Salah satu kemampuan (beli atau jual) harus tetap aktif."
                },
            )

    for field, value in values.items():
        setattr(profile, field, value)

    db.session.commit()
    db.session.refresh(profile)

    return build_profile_payload(user)
