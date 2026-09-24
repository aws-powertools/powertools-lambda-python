import urllib3


def test_inventory_lookup(monkeypatch):
    monkeypatch.setenv("TOKEN_URL", "https://idp.example.com/token")
    monkeypatch.setenv("CLIENT_ID", "orders")
    monkeypatch.setenv("CLIENT_SECRET_NAME", "orders/oauth-secret")
    monkeypatch.setenv("INVENTORY_URL", "https://inventory.example.com")

    from client_credentials import inventory_api, lambda_handler

    def request(method, url, *, timeout):
        assert method == "GET"
        assert url == "https://inventory.example.com/stock/item%2F123"
        assert timeout == 5
        return urllib3.HTTPResponse(body=b'{"stock":12}', status=200)

    monkeypatch.setattr(inventory_api, "request", request)
    assert lambda_handler({"sku": "item/123"}, {}) == {"stock": 12}
