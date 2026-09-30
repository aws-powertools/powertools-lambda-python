import importlib
import sys
from io import BytesIO
from urllib.parse import parse_qs

import urllib3


def test_post_credentials_are_sent_only_to_the_token_endpoint(monkeypatch):
    monkeypatch.setenv("TOKEN_URL", "https://idp.example.com/token")
    monkeypatch.setenv("CLIENT_ID", "orders")
    monkeypatch.setenv("CLIENT_SECRET", "test-only-secret")
    monkeypatch.setenv("INVENTORY_URL", "https://inventory.example.com")
    calls = []

    def request(self, method, url, **options):
        calls.append(url)
        if url == "https://idp.example.com/token":
            assert method == "POST"
            assert options["headers"] == {"Content-Type": "application/x-www-form-urlencoded"}
            assert parse_qs(options["body"].decode()) == {
                "grant_type": ["client_credentials"],
                "scope": ["inventory:read"],
                "client_id": ["orders"],
                "client_secret": ["test-only-secret"],
            }
            return urllib3.HTTPResponse(
                body=BytesIO(b'{"access_token":"test-token","token_type":"Bearer","expires_in":600}'),
                status=200,
                preload_content=False,
            )
        assert method == "GET"
        assert url == "https://inventory.example.com"
        assert options["headers"] == {"Authorization": "Bearer test-token"}
        assert "test-only-secret" not in str(options)
        return urllib3.HTTPResponse(body=BytesIO(b'{"stock":12}'), status=200, preload_content=False)

    monkeypatch.setattr(urllib3.PoolManager, "request", request)
    monkeypatch.delitem(sys.modules, "client_secret_post", raising=False)
    example = importlib.import_module("client_secret_post")

    assert example.lambda_handler({}, {}) == {"stock": 12}
    assert example.lambda_handler({}, {}) == {"stock": 12}
    assert calls == ["https://idp.example.com/token", "https://inventory.example.com", "https://inventory.example.com"]
