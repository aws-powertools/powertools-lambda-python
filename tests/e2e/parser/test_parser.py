import json

import pytest

from tests.e2e.utils import data_fetcher


@pytest.fixture
def handler_with_basic_model_arn(infrastructure: dict) -> str:
    return infrastructure.get("HandlerWithBasicModelArn", "")


@pytest.fixture
def handler_with_union_tag_arn(infrastructure: dict) -> str:
    return infrastructure.get("HandlerWithUnionTagArn", "")


@pytest.fixture
def handler_with_dataclass_arn(infrastructure: dict) -> str:
    return infrastructure.get("HandlerWithDataclass", "")


@pytest.mark.xdist_group(name="parser")
def test_parser_with_basic_model(handler_with_basic_model_arn):
    # GIVEN
    payload = json.dumps({"product": "powertools", "version": "v3"})

    # WHEN
    parser_execution, _ = data_fetcher.get_lambda_response(
        lambda_arn=handler_with_basic_model_arn,
        payload=payload,
    )

    ret = parser_execution["Payload"].read().decode("utf-8")

    assert "powertools" in ret


@pytest.mark.xdist_group(name="parser")
def test_parser_with_union_tag(handler_with_union_tag_arn):
    # GIVEN
    payload = json.dumps({"status": "partial", "error_msg": "partial failure"})

    # WHEN
    parser_execution, _ = data_fetcher.get_lambda_response(
        lambda_arn=handler_with_union_tag_arn,
        payload=payload,
    )

    ret = parser_execution["Payload"].read().decode("utf-8")

    assert "partial failure" in ret


@pytest.mark.xdist_group(name="parser")
def test_parser_with_dataclass(handler_with_dataclass_arn):
    # GIVEN
    payload = json.dumps({"product": "powertools", "version": "v3"})

    # WHEN
    parser_execution, _ = data_fetcher.get_lambda_response(
        lambda_arn=handler_with_dataclass_arn,
        payload=payload,
    )

    ret = parser_execution["Payload"].read().decode("utf-8")

    assert "powertools" in ret
