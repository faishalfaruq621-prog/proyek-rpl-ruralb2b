"""Model tabel ``verification_requests``.

Satu pengajuan verifikasi dimiliki oleh satu business profile. Status
mengikuti enum database: pending, approved, rejected.
"""

from extensions import db


class VerificationRequest(db.Model):
    __tablename__ = "verification_requests"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    business_profile_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "business_profiles.id", ondelete="RESTRICT", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
    )
    status = db.Column(
        db.Enum("pending", "approved", "rejected", name="verification_status"),
        nullable=False,
        default="pending",
        index=True,
    )
    submitted_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )
    reviewed_by = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    business_profile = db.relationship(
        "BusinessProfile",
        back_populates="verification_requests",
        lazy="joined",
    )
    reviewer = db.relationship(
        "User",
        foreign_keys=[reviewed_by],
        lazy="select",
    )
    documents = db.relationship(
        "VerificationDocument",
        back_populates="verification",
        lazy="select",
        order_by="VerificationDocument.id",
    )
    logs = db.relationship(
        "VerificationLog",
        back_populates="verification",
        lazy="select",
        order_by="VerificationLog.id",
    )
    telegram_logs = db.relationship(
        "TelegramLog",
        back_populates="verification",
        lazy="select",
        order_by="TelegramLog.id",
    )

    def to_dict(
        self,
        include_profile: bool = False,
        include_reviewer: bool = False,
        include_documents_count: bool = False,
    ) -> dict:
        data = {
            "id": self.id,
            "business_profile_id": self.business_profile_id,
            "status": self.status,
            "submitted_at": self.submitted_at.isoformat()
            if self.submitted_at
            else None,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat()
            if self.reviewed_at
            else None,
            "rejection_reason": self.rejection_reason,
        }

        if include_profile and self.business_profile is not None:
            data["business_profile"] = self.business_profile.to_dict()
            if self.business_profile.user is not None:
                data["user"] = {
                    "id": self.business_profile.user.id,
                    "full_name": self.business_profile.user.full_name,
                    "email": self.business_profile.user.email,
                }

        if include_reviewer and self.reviewer is not None:
            data["reviewer"] = {
                "id": self.reviewer.id,
                "full_name": self.reviewer.full_name,
                "email": self.reviewer.email,
            }

        if include_documents_count:
            data["documents_count"] = len(self.documents)

        return data

    def __repr__(self) -> str:  # pragma: no cover
        return f"<VerificationRequest {self.id} {self.status}>"
