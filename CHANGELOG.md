# Changelog

All notable changes to `outreply` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] — 2026-04-19

### Added
- `client.posts.publish(...)` — publish a post **immediately** (no scheduling). Synchronous with upstream platform; returns once the platform accepts the post. Accepts the same shape as `posts.schedule` minus `scheduled_at`, plus `media_urls`, `first_comment`, and `tiktok_settings`.

## [1.0.1] — 2026-04-19

### Fixed
- **Breaking field rename**: `client.posts.schedule(publish_at=...)` is now `client.posts.schedule(scheduled_at=...)` to match the server contract. Calls made with 1.0.0 failed with `MISSING_FIELD: scheduled_at is required`. If you upgraded on day one, update your call sites before shipping.

## [1.0.0] — 2026-04-19

### Added
- Initial release.
- `OutReply` client with resources `.account`, `.brands`, `.pages`, `.posts`, `.comments`, `.media`, `.webhooks`.
- Automatic `Idempotency-Key` (UUIDv4) on POST / PATCH / PUT / DELETE — opt out with `idempotency_key=False`.
- Exponential-backoff retries that respect `Retry-After`.
- Typed exceptions: `OutReplyAuthError`, `OutReplyScopeError`, `OutReplyRateLimitError`, `OutReplyQuotaError`, `OutReplyValidationError`, `OutReplyIdempotencyError`, `OutReplyServerError`, `OutReplyConnectionError`.
- `verify_webhook_signature()` / `construct_event()` — stdlib-only HMAC-SHA256 verifier with multi-signature support for 24h secret-rotation grace windows.
- Requires Python 3.9+. Depends on `httpx>=0.27`.
