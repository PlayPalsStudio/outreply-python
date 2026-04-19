"""OutReply client — resource-oriented wrapper."""
from __future__ import annotations

from typing import Any, BinaryIO, List, Mapping, Optional, Union

from ._http import HttpClient


class _Resource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http


class AccountResource(_Resource):
    def retrieve(self) -> dict:
        """Return the authenticated account."""
        return self._http.request("GET", "/account")


class BrandsResource(_Resource):
    def list(self, *, cursor: Optional[str] = None, limit: Optional[int] = None) -> dict:
        return self._http.request("GET", "/brands", params={"cursor": cursor, "limit": limit})


class PagesResource(_Resource):
    def list(
        self,
        *,
        brand_id: Optional[str] = None,
        platform: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> dict:
        return self._http.request(
            "GET",
            "/pages",
            params={"brand_id": brand_id, "platform": platform, "cursor": cursor, "limit": limit},
        )


class PostsResource(_Resource):
    def schedule(
        self,
        *,
        page_id: str,
        message: str,
        scheduled_at: str,
        media_ids: Optional[List[str]] = None,
        link: Optional[str] = None,
        first_comment: Optional[str] = None,
        idempotency_key: Union[str, bool, None] = True,
    ) -> dict:
        """Schedule a new post. Idempotency-safe by default."""
        payload = {
            "page_id": page_id,
            "message": message,
            "scheduled_at": scheduled_at,
            "media_ids": media_ids,
            "link": link,
            "first_comment": first_comment,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._http.request("POST", "/posts/schedule", json=payload, idempotency_key=idempotency_key)

    def publish(
        self,
        *,
        page_id: str,
        message: Optional[str] = None,
        media_ids: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        first_comment: Optional[str] = None,
        tiktok_settings: Optional[Mapping[str, Any]] = None,
        idempotency_key: Union[str, bool, None] = True,
    ) -> dict:
        """Publish a post **immediately** (no scheduling).

        Blocks until the upstream platform accepts the post — expect
        multi-second latency for large media uploads. Idempotency-safe
        by default.
        """
        payload = {
            "page_id": page_id,
            "message": message,
            "media_ids": media_ids,
            "media_urls": media_urls,
            "first_comment": first_comment,
            "tiktok_settings": dict(tiktok_settings) if tiktok_settings is not None else None,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._http.request("POST", "/posts/publish", json=payload, idempotency_key=idempotency_key)

    def list_scheduled(
        self,
        *,
        page_id: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> dict:
        return self._http.request(
            "GET",
            "/posts/scheduled",
            params={"page_id": page_id, "cursor": cursor, "limit": limit},
        )

    def retrieve_scheduled(self, post_id: str) -> dict:
        return self._http.request("GET", f"/posts/scheduled/{post_id}")

    def cancel_scheduled(self, post_id: str) -> None:
        self._http.request("DELETE", f"/posts/scheduled/{post_id}")

    def list_published(
        self,
        *,
        page_id: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> dict:
        return self._http.request(
            "GET",
            "/posts/published",
            params={"page_id": page_id, "cursor": cursor, "limit": limit},
        )


class CommentsResource(_Resource):
    def list(
        self,
        *,
        page_id: Optional[str] = None,
        post_id: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> dict:
        return self._http.request(
            "GET",
            "/comments",
            params={"page_id": page_id, "post_id": post_id, "cursor": cursor, "limit": limit},
        )

    def reply(
        self,
        *,
        comment_id: str,
        message: str,
        idempotency_key: Union[str, bool, None] = True,
    ) -> dict:
        return self._http.request(
            "POST",
            "/comments/reply",
            json={"comment_id": comment_id, "message": message},
            idempotency_key=idempotency_key,
        )


class MediaResource(_Resource):
    def upload(
        self,
        file: Union[BinaryIO, bytes],
        *,
        filename: str,
        mime_type: str = "application/octet-stream",
        idempotency_key: Union[str, bool, None] = True,
    ) -> dict:
        """Upload media via multipart/form-data."""
        files = {"file": (filename, file, mime_type)}
        return self._http.request(
            "POST",
            "/media/upload",
            files=files,
            idempotency_key=idempotency_key,
        )

    def list(self, *, cursor: Optional[str] = None, limit: Optional[int] = None) -> dict:
        return self._http.request("GET", "/media", params={"cursor": cursor, "limit": limit})

    def retrieve(self, media_id: str) -> dict:
        return self._http.request("GET", f"/media/{media_id}")

    def delete(self, media_id: str) -> None:
        self._http.request("DELETE", f"/media/{media_id}")


class WebhooksResource(_Resource):
    def list(self) -> dict:
        return self._http.request("GET", "/webhooks")

    def retrieve(self, webhook_id: str) -> dict:
        return self._http.request("GET", f"/webhooks/{webhook_id}")

    def create(
        self,
        *,
        url: str,
        events: List[str],
        idempotency_key: Union[str, bool, None] = True,
    ) -> dict:
        """Subscribe to events. The returned `secret` is shown only once — store it securely."""
        return self._http.request(
            "POST",
            "/webhooks",
            json={"url": url, "events": events},
            idempotency_key=idempotency_key,
        )

    def delete(self, webhook_id: str) -> None:
        self._http.request("DELETE", f"/webhooks/{webhook_id}")


class OutReply:
    """Main client.

    Example:
        client = OutReply(api_key="outreply_live_...")
        me = client.account.retrieve()
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.outreply.com/api/v1",
        timeout: float = 30.0,
        max_retries: int = 2,
        default_headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self._http = HttpClient(
            api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self.account = AccountResource(self._http)
        self.brands = BrandsResource(self._http)
        self.pages = PagesResource(self._http)
        self.posts = PostsResource(self._http)
        self.comments = CommentsResource(self._http)
        self.media = MediaResource(self._http)
        self.webhooks = WebhooksResource(self._http)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "OutReply":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
