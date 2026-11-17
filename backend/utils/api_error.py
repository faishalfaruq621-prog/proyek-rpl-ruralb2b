"""Exception aplikasi yang otomatis diterjemahkan menjadi response JSON."""


class ApiError(Exception):
    """Error yang aman ditampilkan ke klien.

    :param message: pesan utama untuk pengguna.
    :param status_code: HTTP status code.
    :param errors: detail validasi per field (opsional).
    :param code: kode error mesin (opsional), misalnya ``invalid_credentials``.
    :param details: data tambahan yang aman untuk klien (opsional).
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        errors: dict | None = None,
        code: str | None = None,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or {}
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict:
        payload = {
            "success": False,
            "message": self.message,
        }
        if self.code:
            payload["code"] = self.code
        if self.errors:
            payload["errors"] = self.errors
        if self.details:
            payload["details"] = self.details
        return payload
