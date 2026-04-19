"""Typed errors — 1:1 with the OutReply API error catalog."""
from __future__ import annotations

from typing import Any, Optional


class OutReplyError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str = "UNKNOWN_ERROR",
        status: int = 0,
        request_id: Optional[str] = None,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.request_id = request_id
        self.details = details

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, status={self.status}, message={str(self)!r})"


class OutReplyAuthError(OutReplyError):
    pass


class OutReplyScopeError(OutReplyError):
    pass


class OutReplyRateLimitError(OutReplyError):
    def __init__(self, *args: Any, retry_after_sec: Optional[float] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.retry_after_sec = retry_after_sec


class OutReplyQuotaError(OutReplyError):
    pass


class OutReplyValidationError(OutReplyError):
    pass


class OutReplyIdempotencyError(OutReplyError):
    pass


class OutReplyServerError(OutReplyError):
    pass


class OutReplyConnectionError(OutReplyError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="CONNECTION_ERROR", status=0)


def error_from_response(
    status: int,
    body: Optional[dict],
    retry_after_sec: Optional[float] = None,
) -> OutReplyError:
    code = (body or {}).get("code", "UNKNOWN_ERROR")
    message = (body or {}).get("message", f"HTTP {status}")
    request_id = (body or {}).get("request_id")
    details = (body or {}).get("details")

    kw = dict(code=code, status=status, request_id=request_id, details=details)
    if status == 401:
        return OutReplyAuthError(message, **kw)
    if status == 403:
        return OutReplyScopeError(message, **kw)
    if status == 409 and code.startswith("IDEMPOTENCY"):
        return OutReplyIdempotencyError(message, **kw)
    if status == 422:
        return OutReplyValidationError(message, **kw)
    if status == 429:
        if code == "QUOTA_EXCEEDED":
            return OutReplyQuotaError(message, **kw)
        return OutReplyRateLimitError(message, retry_after_sec=retry_after_sec, **kw)
    if status >= 500:
        return OutReplyServerError(message, **kw)
    return OutReplyError(message, **kw)
