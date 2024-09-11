import pytest
from requests import Request

from tests.e2e.utils import data_fetcher
from tests.e2e.utils.auth import build_iam_auth


@pytest.fixture
def alb_basic_without_body_listener_endpoint(infrastructure: dict) -> str:
    dns_name = infrastructure.get("ALBDnsName")
    port = infrastructure.get("ALBBasicWithoutBodyListenerPort", "")
    return f"http://{dns_name}:{port}"


@pytest.mark.xdist_group(name="event_handler")
def test_alb_with_body_empty(alb_basic_without_body_listener_endpoint):
    # GIVEN url has a trailing slash - it should behave as if there was not one
    url = f"{alb_basic_without_body_listener_endpoint}/todos_with_no_body"

    # WHEN calling an invalid URL (with trailing slash) expect HTTPError exception from data_fetcher
    response = data_fetcher.get_http_response(
        Request(
            method="GET",
            url=url,
            auth=build_iam_auth(url=url, aws_service="lambda"),
        ),
    )

    assert response.status_code == 200
