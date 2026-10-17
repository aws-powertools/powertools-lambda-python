from __future__ import annotations

import pytest

from aws_lambda_powertools.utilities.data_classes.vpc_lattice import VPCLatticeEvent
from tests.functional.utils import load_event


def test_vpc_lattice_event():
    raw_event = load_event("vpcLatticeEvent.json")
    parsed_event = VPCLatticeEvent(raw_event)

    assert parsed_event.raw_path == raw_event["raw_path"]
    assert parsed_event.path == raw_event["raw_path"]
    assert parsed_event.query_string_parameters["order-id"] == "1"
    assert parsed_event.headers["user_agent"] == "curl/7.64.1"
    assert parsed_event.decoded_body == '{"test": "event"}'
    assert parsed_event.json_body == {"test": "event"}
    assert parsed_event.method == raw_event["method"]
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.query_string_parameters == raw_event["query_string_parameters"]
    assert parsed_event.body == raw_event["body"]
    assert parsed_event.is_base64_encoded == raw_event["is_base64_encoded"]


def test_vpc_lattice_event_with_query_string():
    # VPC Lattice sends the query string in raw_path, and parsed in query_string_parameters
    raw_event = load_event("vpcLatticeEventWithQueryString.json")
    parsed_event = VPCLatticeEvent(raw_event)

    assert parsed_event.path == "/testpath"
    assert parsed_event.raw_path == "/testpath?order-id=1"
    assert parsed_event.query_string_parameters == {"order-id": "1"}


@pytest.mark.parametrize(
    "raw_path, expected_path",
    [
        ("/?query1=value1&query2=value2", "/"),
        ("/testpath?", "/testpath"),
        ("/testpath?next=/orders?page=2", "/testpath"),
        ("/files/report%3Fv2?download=true", "/files/report%3Fv2"),
    ],
    ids=["root_path", "empty_query", "question_mark_in_query", "encoded_question_mark_in_path"],
)
def test_vpc_lattice_event_path_excludes_query_string(raw_path, expected_path):
    raw_event = load_event("vpcLatticeEvent.json")
    raw_event["raw_path"] = raw_path
    parsed_event = VPCLatticeEvent(raw_event)

    assert parsed_event.path == expected_path
    assert parsed_event.raw_path == raw_path
