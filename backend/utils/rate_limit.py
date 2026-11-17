"""Rate limiting sederhana untuk endpoint AI.

Menggunakan in-memory store (dict) sehingga tidak memerlukan Redis atau
tabel database baru. Cocok untuk development dan deployment single-instance.
Catatan: blocklist tidak dibagi antar worker dalam deployment multi-worker.
"""

from __future__ import annotations

import time
from collections import defaultdict
from functools import wraps
from typing import Dict

from flask import request
from utils.api_error import ApiError


class RateLimiter:
    """Rate limiter per IP dan endpoint dengan window sliding sederhana."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # key: (ip, endpoint) -> list of timestamps
        self._hits: Dict[str, list[float]] = defaultdict(list)

    def _clean(self, key: str, now: float) -> None:
        """Menghapus timestamp di luar window."""
        cutoff = now - self.window_seconds
        self._hits[key] = [t for t in self._hits[key] if t > cutoff]

    def is_allowed(self, key: str) -> bool:
        """Mengembalikan True jika request diizinkan, False jika terlambat."""
        now = time.time()
        self._clean(key, now)
        if len(self._hits[key]) >= self.max_requests:
            return False
        self._hits[key].append(now)
        return True


# Rate limiter untuk endpoint AI: 50 request per menit per IP per endpoint
ai_rate_limiter = RateLimiter(max_requests=50, window_seconds=60)

# Rate limiter untuk endpoint AI yang lebih ketat: 10 request per menit
ai_strict_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


def ai_rate_limit(view):
    """Decorator rate limiting untuk endpoint AI chat."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        ip = request.remote_addr or "unknown"
        endpoint = request.endpoint or "unknown"
        key = f"{ip}:{endpoint}"
        if not ai_rate_limiter.is_allowed(key):
            raise ApiError(
                "Terlalu banyak permintaan ke layanan AI. Silakan coba lagi "
                "beberapa saat.",
                status_code=429,
                code="ai_rate_limited",
            )
        return view(*args, **kwargs)

    return wrapped


def ai_strict_rate_limit(view):
    """Decorator rate limiting ketat untuk endpoint AI yang intensif."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        ip = request.remote_addr or "unknown"
        endpoint = request.endpoint or "unknown"
        key = f"{ip}:{endpoint}"
        if not ai_strict_rate_limiter.is_allowed(key):
            raise ApiError(
                "Terlalu banyak permintaan ke layanan AI. Silakan coba lagi "
                "beberapa saat.",
                status_code=429,
                code="ai_rate_limited",
            )
        return view(*args, **kwargs)

    return wrapped
