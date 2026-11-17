"""Model tabel ``business_profiles``.

Profil bisnis terhubung satu-ke-satu dengan ``users``. Jenis akun bisnis
disimpan di kolom ``business_type`` sesuai enum yang sudah ada di database.
"""

from extensions import db


class BusinessProfile(db.Model):
    __tablename__ = "business_profiles"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    business_name = db.Column(db.String(180), nullable=False)
    business_type = db.Column(
        db.Enum(
            "farmer",
            "supplier",
            "collector",
            "producer",
            "shop",
            "warung",
            "other",
            name="business_type",
        ),
        nullable=False,
    )
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.Text, nullable=True)
    village = db.Column(db.String(120), nullable=True)
    district = db.Column(db.String(120), nullable=True)
    city = db.Column(db.String(120), nullable=True)
    province = db.Column(db.String(120), nullable=True)
    postal_code = db.Column(db.String(15), nullable=True)
    latitude = db.Column(db.Numeric(10, 7), nullable=True)
    longitude = db.Column(db.Numeric(10, 7), nullable=True)
    description = db.Column(db.Text, nullable=True)
    # Kemampuan akun, ditambahkan lewat migrations/001. Default 1
    # sesuai demonstrasi konsensus migrasi (tidak mengunci akun lama).
    can_buy = db.Column(db.Boolean, nullable=False, default=True)
    can_sell = db.Column(db.Boolean, nullable=False, default=True)
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

    user = db.relationship("User", back_populates="business_profile")
    verification_requests = db.relationship(
        "VerificationRequest",
        back_populates="business_profile",
        lazy="select",
    )
    products = db.relationship(
        "Product",
        back_populates="business_profile",
        lazy="select",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "business_name": self.business_name,
            "business_type": self.business_type,
            # Kemampuan akun dipublikasikan bersama profil agar frontend
            # dan backend membaca sumber yang sama.
            "capabilities": {"can_buy": bool(self.can_buy), "can_sell": bool(self.can_sell)},
            "can_buy": bool(self.can_buy),
            "can_sell": bool(self.can_sell),
            "phone": self.phone,
            "address": self.address,
            "village": self.village,
            "district": self.district,
            "city": self.city,
            "province": self.province,
            "postal_code": self.postal_code,
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "longitude": float(self.longitude) if self.longitude is not None else None,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return f"<BusinessProfile {self.id} user={self.user_id}>"
