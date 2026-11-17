"""Service chat Buyer-Seller.

Aturan akses: hanya pembeli dan penjual dalam satu percakapan yang dapat
melihat percakapan dan mengirim/membaca pesan. Referensi percakapan bisa
berupa produk (pembeli memulai dari halaman produk) atau pesanan.
Percakapan dibuat idempotent lewat scope_key unik, dan pesan baru
memicu satu notifikasi untuk lawan bicara (dedupe per pesan).
"""

from extensions import db
from models import BusinessProfile, Conversation, Message, Order, Product, User
from services.notification_service import create_notification
from utils.api_error import ApiError

MAX_BODY_LENGTH = 2000

_CONVERSATION_OPTIONS = (
    db.joinedload(Conversation.buyer).joinedload(User.business_profile),
    db.joinedload(Conversation.seller).joinedload(User.business_profile),
    db.joinedload(Conversation.product),
)


def _get_conversation_for_user(conversation_id: int, user) -> Conversation:
    statement = (
        db.select(Conversation)
        .options(
            *_CONVERSATION_OPTIONS,
            db.selectinload(Conversation.messages).joinedload(Message.sender),
        )
        .where(Conversation.id == conversation_id)
    )
    conversation = db.session.scalar(statement)
    if conversation is None or not conversation.is_participant(user):
        # 404 juga untuk percakapan milik orang lain: keberadaan data
        # pihak ketiga tidak boleh bisa dikonfirmasi.
        raise ApiError(
            "Percakapan tidak ditemukan.",
            status_code=404,
            code="conversation_not_found",
        )
    return conversation


def _build_scope_product(product: Product, buyer_id: int, seller_id: int) -> str:
    return f"p:{product.id}:{buyer_id}:{seller_id}"


def _resolve_participants_for_product(product: Product, user) -> tuple[int, int]:
    if product.business_profile is None:
        raise ApiError(
            "Produk tidak memiliki penjual yang valid.",
            status_code=409,
            code="product_seller_missing",
        )
    seller_id = product.business_profile.user_id
    buyer_id = user.id
    if buyer_id == seller_id:
        # Pembeli mencoba chat produk miliknya sendiri: pindahkan sisi
        # pembeli tetap buyer (akun dual), tapi tolak self-chat.
        raise ApiError(
            "Tidak dapat memulai percakapan dengan diri sendiri.",
            status_code=409,
            code="self_conversation",
        )
    return buyer_id, seller_id


def _resolve_participants_for_order(order: Order, user) -> tuple[int, int]:
    if order.buyer_id != user.id and order.seller_id != user.id:
        # Sama seperti endpoint pesanan lain: 404 agar tidak membocorkan.
        raise ApiError(
            "Pesanan tidak ditemukan.",
            status_code=404,
            code="order_not_found",
        )
    seller_user_id = db.session.scalar(
        db.select(BusinessProfile.user_id).where(
            BusinessProfile.id == order.seller_id
        )
    )
    if seller_user_id is None:
        raise ApiError(
            "Penjual tidak ditemukan.",
            status_code=404,
            code="seller_not_found",
        )
    buyer_id, seller_id = order.buyer_id, seller_user_id
    if buyer_id == seller_id:
        raise ApiError(
            "Tidak dapat memulai percakapan dengan diri sendiri.",
            status_code=409,
            code="self_conversation",
        )
    return buyer_id, seller_id


def _get_or_create_conversation(
    scope_key: str, product_id: int | None, order_id: int | None,
    buyer_id: int, seller_id: int,
) -> Conversation:
    conversation = db.session.scalar(
        db.select(Conversation).where(Conversation.scope_key == scope_key)
    )
    if conversation is None:
        conversation = Conversation(
            scope_key=scope_key,
            product_id=product_id,
            order_id=order_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
        )
        db.session.add(conversation)
        try:
            db.session.flush()
        except Exception:
            db.session.rollback()
            # Race condition: request lain mungkin sudah membuat scope ini.
            conversation = db.session.scalar(
                db.select(Conversation).where(Conversation.scope_key == scope_key)
            )
            if conversation is None:
                raise ApiError(
                    "Gagal membuat percakapan.",
                    status_code=500,
                    code="conversation_create_failed",
                )
    return conversation


def start_or_get_conversation(user, data: dict) -> dict:
    """Payload: product_id atau order_id (satu saja). Mengembalikan percakapan.

    Buyer dalam percakapan adalah pembeli pada konteks:
    - product: g.current_user (pembeli) vs pemilik produk.
    - order:   buyer_id dari pesanan vs user_id profil penjual; pemanggil
               adalah salah satu dari keduanya (divalidasi).
    """
    if not isinstance(data, dict):
        raise ApiError(
            "Payload tidak valid.",
            status_code=422,
            errors={"_request": "Body JSON diperlukan."},
        )
    product_id = data.get("product_id")
    order_id = data.get("order_id")
    if (product_id is None) == (order_id is None):
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={"_request": "Kirim product_id atau order_id (satu saja)."},
        )

    if product_id is not None:
        product = db.session.scalar(
            db.select(Product).where(Product.id == product_id)
        )
        if product is None:
            raise ApiError(
                "Produk tidak ditemukan.",
                status_code=404,
                code="product_not_found",
            )
        buyer_id, seller_id = _resolve_participants_for_product(product, user)
        scope_key = _build_scope_product(product, buyer_id, seller_id)
        conversation = _get_or_create_conversation(
            scope_key, product_id, None, buyer_id, seller_id
        )
    else:
        order = db.session.scalar(db.select(Order).where(Order.id == order_id))
        if order is None:
            raise ApiError(
                "Pesanan tidak ditemukan.",
                status_code=404,
                code="order_not_found",
            )
        buyer_id, seller_id = _resolve_participants_for_order(order, user)
        scope_key = f"o:{order.id}"
        conversation = _get_or_create_conversation(
            scope_key, None, order.id, buyer_id, seller_id
        )

    conversation = _get_conversation_for_user(conversation.id, user)
    db.session.commit()
    return conversation.to_dict(include_last=True)


def list_conversations(user, page: int, per_page: int) -> tuple[list, object]:
    statement = (
        db.select(Conversation)
        .options(
            *_CONVERSATION_OPTIONS,
            db.selectinload(Conversation.messages).joinedload(Message.sender),
        )
        .where(
            (Conversation.buyer_id == user.id) | (Conversation.seller_id == user.id)
        )
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
    )
    pagination = db.paginate(statement, page=page, per_page=per_page, error_out=False)
    items = [conv.to_dict(include_last=True) for conv in pagination.items]
    return items, pagination


def get_conversation(user, conversation_id: int) -> dict:
    conversation = _get_conversation_for_user(conversation_id, user)
    return conversation.to_dict(include_last=True)


def get_messages(user, conversation_id: int, page: int, per_page: int) -> tuple[list, object]:
    _get_conversation_for_user(conversation_id, user)
    statement = (
        db.select(Message)
        .options(db.joinedload(Message.sender))
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
    )
    pagination = db.paginate(statement, page=page, per_page=per_page, error_out=False)
    items = [msg.to_dict() for msg in pagination.items]
    return items, pagination


def _notify_recipients(conversation: Conversation, sender_id: int, message: Message) -> None:
    title = "Pesan baru"
    product_name = (
        conversation.product.product_name if conversation.product else None
    )
    detail = f"Pesan baru dari chat{' produk ' + product_name if product_name else ' pesanan'}."
    for recipient_id in conversation.participant_ids():
        if recipient_id == sender_id:
            continue
        create_notification(
            user_id=recipient_id,
            title=title,
            message=detail,
            type_="chat",
            link="/chat/" + str(conversation.id),
            dedupe_key=f"msg:{message.id}",
        )


def send_message(user, conversation_id: int, data: dict) -> dict:
    conversation = _get_conversation_for_user(conversation_id, user)
    body = data.get("body") if isinstance(data, dict) else None
    if not isinstance(body, str) or not body.strip():
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={"body": "Isi pesan wajib diisi."},
        )
    body = body.strip()
    if len(body) > MAX_BODY_LENGTH:
        raise ApiError(
            "Validasi gagal.",
            status_code=422,
            errors={"body": f"Pesan maksimal {MAX_BODY_LENGTH} karakter."},
        )

    message = Message(conversation_id=conversation.id, sender_id=user.id, body=body)
    db.session.add(message)
    db.session.flush()
    _notify_recipients(conversation, user.id, message)
    db.session.commit()
    return message.to_dict()
