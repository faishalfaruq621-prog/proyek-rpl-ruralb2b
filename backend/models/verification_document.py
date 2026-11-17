"""Model tabel ``verification_documents``.

``file_path`` menyimpan path relatif terhadap direktori penyimpanan privat,
bukan path absolut dan bukan URL publik.
"""

from pathlib import Path

from extensions import db


class VerificationDocument(db.Model):
    __tablename__ = "verification_documents"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    verification_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "verification_requests.id", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
    )
    document_type = db.Column(db.String(80), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    verification = db.relationship(
        "VerificationRequest",
        back_populates="documents",
    )

    def to_dict(self) -> dict:
        suffix = Path(self.file_path).suffix.lower()
        return {
            "id": self.id,
            "verification_id": self.verification_id,
            "document_type": self.document_type,
            "file_name": f"{self.document_type}_{self.id}{suffix}",
            "uploaded_at": self.uploaded_at.isoformat()
            if self.uploaded_at
            else None,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<VerificationDocument {self.id} {self.document_type}>"
