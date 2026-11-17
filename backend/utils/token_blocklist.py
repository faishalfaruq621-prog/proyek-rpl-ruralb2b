"""Blocklist token untuk mendukung logout.

Catatan penting:
- Skema database tidak diubah pada tahap ini, sehingga blocklist disimpan
  di memori proses (thread-safe).
- Blocklist akan kosong lagi setelah server restart dan tidak dibagi antar
  worker. Untuk produksi multi-worker, ganti implementasi ini dengan Redis
  atau tabel database khusus blocklist.
"""

import threading
import time

_lock = threading.Lock()
_revoked_tokens: dict[str, int] = {}


def _to_timestamp(value) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    if hasattr(value, "timestamp"):
        return int(value.timestamp())
    return int(value)


def revoke_token(jti: str, expires_at) -> None:
    """Menandai token sebagai tidak valid sampai waktu kedaluwarsanya."""

    if not jti:
        return

    expires_timestamp = _to_timestamp(expires_at)
    now = int(time.time())

    with _lock:
        # Bersihkan entri yang sudah kedaluwarsa agar memori tidak tumbuh.
        for token_id, expiry in list(_revoked_tokens.items()):
            if expiry <= now:
                del _revoked_tokens[token_id]
        _revoked_tokens[jti] = expires_timestamp


def is_token_revoked(jti: str) -> bool:
    if not jti:
        return False

    now = int(time.time())
    with _lock:
        expiry = _revoked_tokens.get(jti)
        if expiry is None:
            return False
        if expiry <= now:
            del _revoked_tokens[jti]
            return False
        return True
