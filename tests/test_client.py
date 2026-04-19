"""Client tests using pytest-httpx."""
import pytest

from outreply import (
    OutReply,
    OutReplyAuthError,
    OutReplyValidationError,
)


@pytest.fixture
def client():
    c = OutReply(api_key="outreply_test_x", max_retries=0)
    yield c
    c.close()


def test_bearer_auth_and_idempotency(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.outreply.com/api/v1/posts/schedule",
        method="POST",
        json={"id": "p_1"},
        status_code=200,
    )
    client.posts.schedule(
        page_id="page_1",
        message="hi",
        publish_at="2026-05-01T10:00:00Z",
    )
    req = httpx_mock.get_requests()[-1]
    assert req.headers["authorization"] == "Bearer outreply_test_x"
    assert "idempotency-key" in req.headers


def test_401_maps_to_auth_error(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.outreply.com/api/v1/account",
        method="GET",
        json={"code": "INVALID_TOKEN", "message": "bad key"},
        status_code=401,
    )
    with pytest.raises(OutReplyAuthError):
        client.account.retrieve()


def test_422_maps_to_validation_error(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.outreply.com/api/v1/posts/schedule",
        method="POST",
        json={"code": "VALIDATION_ERROR", "message": "bad", "details": {"field": "page_id"}},
        status_code=422,
    )
    with pytest.raises(OutReplyValidationError):
        client.posts.schedule(page_id="", message="", publish_at="")
