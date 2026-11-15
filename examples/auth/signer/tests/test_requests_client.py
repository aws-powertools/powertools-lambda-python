import json

import requests


def test_orders_call_is_signed(monkeypatch):
    # GIVEN the Lambda environment
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAEXAMPLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "example")  # noqa: S105 test value
    monkeypatch.setenv("ORDERS_API_URL", "https://abc123.execute-api.us-east-1.amazonaws.com/prod")

    from requests_client import http, lambda_handler

    sent = {}

    def fake_send(self, request, **kwargs):
        sent["request"] = request
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps({"order_id": "o-1"}).encode()
        return response

    monkeypatch.setattr(requests.Session, "send", fake_send)

    # WHEN the handler calls the API
    assert lambda_handler({"customer_id": "c-9"}, {}) == {"order_id": "o-1"}

    # THEN the request left with a SigV4 signature over the JSON body
    request = sent["request"]
    assert request.headers["Authorization"].startswith("AWS4-HMAC-SHA256 Credential=AKIAEXAMPLE/")
    assert "X-Amz-Date" in request.headers
    assert json.loads(request.body) == {"customer_id": "c-9"}
    assert http.auth is not None
