"""Model tabel ``users``.

Struktur kolom mengikuti tabel MySQL yang sudah ada. Jangan mengubah
definisi kolom tanpa migrasi dan persetujuan.
"""

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(190), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum("business_user", "admin", name="role"),
        nullable=False,
        default="business_user",
    )
    account_status = db.Column(
        db.Enum("active", "suspended", "inactive", name="account_status"),
        nullable=False,
        default="active",
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
        server_onupdate=db.text("CURRENT_TIMESTAMP"),
    )

    business_profile = db.relationship(
        "BusinessProfile",
        back_populates="user",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    notifications = db.relationship(
        "Notification",
        back_populates="user",
        lazy="select",
    )
    conversations_as_buyer = db.relationship(
        "Conversation",
        foreign_keys="Conversation.buyer_id",
        back_populates="buyer",
        lazy="select",
    )
    conversations_as_seller = db.relationship(
        "Conversation",
        foreign_keys="Conversation.seller_id",
        back_populates="seller",
        lazy="select",
    )

    def set_password(self, password: str) -> None:
        """Menyimpan hash password, bukan password asli."""

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Representasi aman untuk API. ``password_hash`` tidak pernah ikut."""

        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "account_status": self.account_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "business_profile": (
                self.business_profile.to_dict() if self.business_profile else None
            ),
        }

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return f"<User {self.id} {self.email}>"
