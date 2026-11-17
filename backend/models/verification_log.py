"""Model tabel ``verification_logs``.

Log mencatat perubahan status verifikasi, termasuk pembuatan pengajuan
(old_status NULL -> pending) dan keputusan admin.
"""

from extensions import db


class VerificationLog(db.Model):
    __tablename__ = "verification_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    verification_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "verification_requests.id", ondelete="RESTRICT", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
    )
    admin_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    old_status = db.Column(
        db.Enum("pending", "approved", "rejected", name="verification_status"),
        nullable=True,
    )
    new_status = db.Column(
        db.Enum("pending", "approved", "rejected", name="verification_status"),
        nullable=False,
    )
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    verification = db.relationship(
        "VerificationRequest",
        back_populates="logs",
    )
    admin = db.relationship(
        "User",
        foreign_keys=[admin_id],
        lazy="select",
    )

    def to_dict(self, include_admin: bool = False) -> dict:
        data = {
            "id": self.id,
            "verification_id": self.verification_id,
            "admin_id": self.admin_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_admin:
            data["admin"] = (
                {
                    "id": self.admin.id,
                    "full_name": self.admin.full_name,
                    "email": self.admin.email,
                }
                if self.admin is not None
                else None
            )
        return data

    def __repr__(self) -> str:  # pragma: no cover
        return f"<VerificationLog {self.id} {self.new_status}>"
