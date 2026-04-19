# outreply

Official Python SDK for the [OutReply Developer API](https://outreply.com/developers).

```bash
pip install outreply
```

## Quick start

```python
import os
from outreply import OutReply

client = OutReply(api_key=os.environ["OUTREPLY_API_KEY"])

# 1. Verify your key
me = client.account.retrieve()
print(f"Signed in as {me['email']}")

# 2. Schedule a post (idempotency-safe — retry freely)
post = client.posts.schedule(
    page_id="65f...",
    message="Launching tomorrow 🚀",
    scheduled_at="2026-05-01T10:00:00Z",
)

# 2b. …or publish one right now.
live = client.posts.publish(
    page_id="65f...",
    message="We're live! 🎉",
    media_urls=["https://cdn.example.com/hero.jpg"],
)
print(live["platform_post_id"])

# 3. Subscribe to real-time events
hook = client.webhooks.create(
    url="https://example.com/webhooks/outreply",
    events=["post.published", "post.failed"],
)
print("Store this secret — it's shown only once:", hook["secret"])
```

## Features

- 🔐 Bearer-token auth. Supports scoped keys and sandbox tokens.
- 🔁 Automatic `Idempotency-Key` on every mutating call.
- 🪝 Built-in webhook signature verifier.
- ⏱ Exponential-backoff retries that respect `Retry-After`.
- 🧯 Typed exceptions mapped 1:1 with the [error catalog](https://outreply.com/api/v1/errors).
- 🧭 Full type hints. Works on Python 3.9+.

## Resources

| Namespace | Methods |
|-----------|---------|
| `client.account` | `retrieve()` |
| `client.brands` | `list()` |
| `client.pages` | `list(brand_id=..., platform=...)` |
| `client.posts` | `schedule()`, `list_scheduled()`, `retrieve_scheduled()`, `cancel_scheduled()`, `list_published()` |
| `client.comments` | `list()`, `reply()` |
| `client.media` | `upload()`, `list()`, `retrieve()`, `delete()` |
| `client.webhooks` | `list()`, `retrieve()`, `create()`, `delete()` |

## Webhook verification (Flask)

```python
from flask import Flask, request, abort
from outreply import construct_event

app = Flask(__name__)

@app.post("/webhooks/outreply")
def outreply_webhook():
    try:
        event = construct_event(
            payload=request.get_data(),  # raw bytes — NOT request.json
            header=request.headers.get("X-OutReply-Signature"),
            secret=os.environ["OUTREPLY_WEBHOOK_SECRET"],
            timestamp_header=request.headers.get("X-OutReply-Timestamp"),
            tolerance_sec=300,
        )
    except ValueError:
        abort(400)
    print("Received:", event["type"], event["data"])
    return "", 200
```

The verifier is dual-signature aware — it accepts comma-separated signatures so your receiver keeps accepting traffic during a 24-hour secret-rotation grace window.

## Error handling

```python
from outreply import (
    OutReply,
    OutReplyRateLimitError,
    OutReplyValidationError,
    OutReplyQuotaError,
)

try:
    client.posts.schedule(page_id="...", message="...", scheduled_at="...")
except OutReplyValidationError as err:
    print("Bad input:", err.details)
except OutReplyRateLimitError as err:
    print(f"Slow down — retry in {err.retry_after_sec}s")
except OutReplyQuotaError:
    print("Daily quota exceeded. Upgrade your plan.")
```

## Configuration

```python
client = OutReply(
    api_key=os.environ["OUTREPLY_API_KEY"],
    timeout=30.0,
    max_retries=2,              # 3 attempts total
    default_headers={"X-Tenant": "acme-co"},
)
```

## License

MIT © OutReply
