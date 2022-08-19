import pytest
from requests import Request

from tests.e2e.utils import data_fetcher


@pytest.fixture
def alb_endpoint(infrastructure: dict) -> str:
    dns_name = infrastructure.get("ALBDnsName")
    return f"http://{dns_name}"


def test_alb_headers_serializer(alb_endpoint):
    # GIVEN
    url = f"{alb_endpoint}/todos"

    # WHEN
    response = data_fetcher.get_http_response(Request(method="GET", url=url))

    # THEN
    assert response.status_code == 200
    assert response.content == "Hello world"
    assert response.headers["content-type"] == "text/plain"

    assert response.headers["Foo"] == "zbr"

    assert "MonsterCookie" in response.cookies
    assert "CookieMonster; Secure" not in response.cookies
