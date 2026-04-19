"""Webhook signature verification — zero extra dependencies."""
from __future__ import annotations

import hmac
import json
import time
from hashlib import sha256
from typing import Optional, Union


def _compute(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), payload, sha256).hexdigest()


def _as_bytes(payload: Union[str, bytes]) -> bytes:
    return payload if isinstance(payload, (bytes, bytearray)) else payload.encode("utf-8")


def verify_webhook_signature(
    payload: Union[str, bytes],
    header: Optional[str],
    secret: str,
    *,
    timestamp_header: Optional[str] = None,
    tolerance_sec: Optional[float] = None,
) -> bool:
    """Return ``True`` when the signature is valid, else ``False``.

    Accepts multi-signature headers (comma-separated) emitted during a
    24-hour secret-rotation grace window.
    """
    if not header or not secret:
        return False

    if tolerance_sec is not None:
        if not timestamp_header:
            return False
        try:
            ts = float(timestamp_header)
        except ValueError:
            return False
        if abs(time.time() - ts) > tolerance_sec:
            return False

    expected = _compute(secret, _as_bytes(payload))
    candidates = [s.strip() for s in header.split(",") if s.strip()]
    for candidate in candidates:
        value = candidate[7:] if candidate.startswith("sha256=") else candidate
        if hmac.compare_digest(value, expected):
            return True
    return False


def construct_event(
    payload: Union[str, bytes],
    header: Optional[str],
    secret: str,
    *,
    timestamp_header: Optional[str] = None,
    tolerance_sec: Optional[float] = None,
) -> dict:
    """Verify and parse a webhook payload. Raises ``ValueError`` on failure."""
    if not verify_webhook_signature(
        payload,
        header,
        secret,
        timestamp_header=timestamp_header,
        tolerance_sec=tolerance_sec,
    ):
        raise ValueError("OutReply webhook signature verification failed.")
    body = payload if isinstance(payload, str) else payload.decode("utf-8")
    return json.loads(body)
