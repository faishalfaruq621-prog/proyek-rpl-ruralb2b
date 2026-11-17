"""Model tabel ``conversations`` dan ``messages`` (chat Buyer-Seller).

Satu percakapan per kombinasi pembeli-penjual dengan referensi produk
atau pesanan, dikunci lewat ``scope_key`` unik agar tidak ada
percakapan ganda untuk konteks yang sama.
"""

from extensions import db


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    scope_key = db.Column(db.String(80), nullable=False, unique=True)
    product_id = db.Column(
        db.BigInteger,
        db.ForeignKey("products.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    order_id = db.Column(
        db.BigInteger,
        db.ForeignKey("orders.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    buyer_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
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

    product = db.relationship("Product")
    order = db.relationship("Order")
    buyer = db.relationship(
        "User", foreign_keys=[buyer_id], back_populates="conversations_as_buyer"
    )
    seller = db.relationship(
        "User", foreign_keys=[seller_id], back_populates="conversations_as_seller"
    )
    messages = db.relationship(
        "Message",
        back_populates="conversation",
        lazy="select",
        order_by="Message.created_at.asc(), Message.id.asc()",
    )

    def is_participant(self, user) -> bool:
        return user is not None and user.id in (self.buyer_id, self.seller_id)

    def participant_ids(self) -> tuple[int, int]:
        return self.buyer_id, self.seller_id

    def to_dict(self, include_last: bool = True) -> dict:
        data = {
            "id": self.id,
            "product_id": self.product_id,
            "order_id": self.order_id,
            "buyer": {
                "id": self.buyer.id,
                "full_name": self.buyer.full_name,
                "business_name": (
                    self.buyer.business_profile.business_name
                    if self.buyer.business_profile
                    else None
                ),
            },
            "seller": {
                "id": self.seller.id,
                "full_name": self.seller.full_name,
                "business_name": (
                    self.seller.business_profile.business_name
                    if self.seller.business_profile
                    else None
                ),
            },
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
        }
        if self.product is not None:
            data["product"] = {
                "id": self.product.id,
                "product_name": self.product.product_name,
            }
        last = self.messages[-1] if self.messages else None
        if include_last:
            data["last_message"] = last.to_dict() if last else None
            data["message_count"] = len(self.messages)
        return data


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    conversation_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "conversations.id", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
    )
    sender_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    body = db.Column(db.String(2000), nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    conversation = db.relationship("Conversation", back_populates="messages")
    sender = db.relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender": {
                "id": self.sender.id,
                "full_name": self.sender.full_name,
                "role": self.sender.role,
            },
            "body": self.body,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
