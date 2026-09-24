import runpy
from pathlib import Path

import pytest
import urllib3

from aws_lambda_powertools.utilities.auth_alpha import OAuth2Client

EXAMPLE = Path(__file__).parents[1] / "src" / "headers.py"


@pytest.fixture
def example_environment(monkeypatch):
    monkeypatch.setenv("TOKEN_URL", "https://idp.example.com/token")
    monkeypatch.setenv("CLIENT_ID", "orders")
    monkeypatch.setenv("CLIENT_SECRET", "test-secret")


@pytest.mark.parametrize(
    "destination",
    [
        "http://inventory.example.com",
        "//inventory.example.com",
        "https:///inventory",
        "https://user:password@inventory.example.com",
        "https://inventory.example.com/#fragment",
    ],
)
def test_unsafe_destinations_are_rejected_before_obtaining_headers(example_environment, monkeypatch, destination):
    monkeypatch.setenv("INVENTORY_URL", destination)
    acquired = []
    requests = []

    def auth_headers(self):
        acquired.append(True)
        return {"Authorization": "Bearer test-token"}

    def request(self, method, url, **options):
        requests.append(url)
        return urllib3.HTTPResponse(body=b'{"stock":12}', status=200)

    monkeypatch.setattr(OAuth2Client, "auth_headers", auth_headers)
    monkeypatch.setattr(urllib3.PoolManager, "request", request)
    example_path = str(EXAMPLE)

    with pytest.raises(ValueError, match="INVENTORY_URL"):
        runpy.run_path(example_path)

    assert acquired == []
    assert requests == []


def test_https_destination_receives_the_token_with_safe_transport_options(example_environment, monkeypatch):
    monkeypatch.setenv("INVENTORY_URL", "https://inventory.example.com")
    monkeypatch.setattr(OAuth2Client, "auth_headers", lambda self: {"Authorization": "Bearer test-token"})
    requests = []

    def request(self, method, url, **options):
        requests.append((method, url))
        assert options["headers"] == {"Authorization": "Bearer test-token"}
        assert options["timeout"].total == 5
        assert options["redirect"] is False
        assert options["retries"] is False
        return urllib3.HTTPResponse(body=b'{"stock":12}', status=200)

    monkeypatch.setattr(urllib3.PoolManager, "request", request)
    example = runpy.run_path(str(EXAMPLE))

    assert example["lambda_handler"]({"sku": "item/123"}, {}) == {"stock": 12}
    assert requests == [("GET", "https://inventory.example.com/stock/item%2F123")]
