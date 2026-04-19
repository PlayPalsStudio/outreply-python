"""Webhook verifier tests — no network required."""
import hmac
import json
import time
from hashlib import sha256

import pytest

from outreply import construct_event, verify_webhook_signature


SECRET = "whsec_test_abc123"
PAYLOAD = json.dumps({"id": "evt_1", "type": "post.published", "data": {}})
SIG = hmac.new(SECRET.encode(), PAYLOAD.encode(), sha256).hexdigest()


def test_valid_signature():
    assert verify_webhook_signature(PAYLOAD, SIG, SECRET) is True


def test_sha256_prefix_accepted():
    assert verify_webhook_signature(PAYLOAD, f"sha256={SIG}", SECRET) is True


def test_multi_signature_rotation_grace():
    header = f"deadbeef, sha256={SIG}"
    assert verify_webhook_signature(PAYLOAD, header, SECRET) is True


def test_invalid_signature_rejected():
    assert verify_webhook_signature(PAYLOAD, "bad", SECRET) is False


def test_stale_timestamp_rejected():
    old_ts = str(int(time.time()) - 3600)
    assert (
        verify_webhook_signature(
            PAYLOAD,
            SIG,
            SECRET,
            timestamp_header=old_ts,
            tolerance_sec=300,
        )
        is False
    )


def test_construct_event_success():
    event = construct_event(PAYLOAD, SIG, SECRET)
    assert event["type"] == "post.published"


def test_construct_event_raises_on_bad_signature():
    with pytest.raises(ValueError):
        construct_event(PAYLOAD, "nope", SECRET)
