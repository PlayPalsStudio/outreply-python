"""Internal HTTP client."""
from __future__ import annotations

import random
import time
import uuid
from typing import Any, Dict, Mapping, Optional, Tuple, Union

import httpx

from .errors import OutReplyConnectionError, error_from_response

DEFAULT_BASE = "https://api.outreply.com/api/v1"
SDK_VERSION = "1.0.0"
MUTATING = {"POST", "PATCH", "PUT", "DELETE"}


class HttpClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE,
        timeout: float = 30.0,
        max_retries: int = 2,
        default_headers: Optional[Mapping[str, str]] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        if not api_key:
            raise ValueError("OutReply SDK: api_key is required.")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max(0, max_retries)
        self._extra_headers = dict(default_headers or {})
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        files: Any = None,
        idempotency_key: Union[str, bool, None] = True,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        method = method.upper()
        url = f"{self._base_url}{path}"

        request_headers: Dict[str, str] = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "User-Agent": f"outreply-python/{SDK_VERSION}",
            **self._extra_headers,
            **dict(headers or {}),
        }

        if method in MUTATING:
            key = None
            if idempotency_key is True:
                key = str(uuid.uuid4())
            elif isinstance(idempotency_key, str):
                key = idempotency_key
            if key:
                request_headers["Idempotency-Key"] = key

        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        attempt = 0
        while True:
            try:
                response = self._client.request(
                    method,
                    url,
                    params=clean_params or None,
                    json=json,
                    files=files,
                    headers=request_headers,
                )
            except httpx.RequestError as exc:
                if attempt < self._max_retries:
                    time.sleep(self._backoff(attempt))
                    attempt += 1
                    continue
                raise OutReplyConnectionError(str(exc)) from exc

            retry_after = self._parse_retry_after(response.headers.get("retry-after"))

            if 200 <= response.status_code < 300:
                if response.status_code == 204 or not response.content:
                    return None
                ctype = response.headers.get("content-type", "")
                if "application/json" in ctype:
                    return response.json()
                return response.text

            body: Optional[dict] = None
            try:
                body = response.json()
            except ValueError:
                body = None

            if attempt < self._max_retries and (response.status_code == 429 or response.status_code >= 500):
                wait = retry_after if retry_after else self._backoff(attempt)
                time.sleep(wait)
                attempt += 1
                continue

            raise error_from_response(response.status_code, body, retry_after)

    @staticmethod
    def _backoff(attempt: int) -> float:
        base = min(0.5 * (2 ** attempt), 8.0)
        return base + random.uniform(0, 0.25)

    @staticmethod
    def _parse_retry_after(value: Optional[str]) -> Optional[float]:
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None
