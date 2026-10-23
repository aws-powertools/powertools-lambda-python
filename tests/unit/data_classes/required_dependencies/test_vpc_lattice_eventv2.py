from __future__ import annotations

import pytest

from aws_lambda_powertools.utilities.data_classes.vpc_lattice import VPCLatticeEventV2
from aws_lambda_powertools.warnings import PowertoolsDeprecationWarning
from tests.functional.utils import load_event


def test_vpc_lattice_v2_event():
    raw_event = load_event("vpcLatticeV2Event.json")
    parsed_event = VPCLatticeEventV2(raw_event)

    assert parsed_event.path == raw_event["path"]
    assert parsed_event.query_string_parameters["order-id"] == "1"
    assert parsed_event.headers["user_agent"] == "curl/7.64.1"
    assert parsed_event.decoded_body == '{"message": "Hello from Lambda!"}'
    assert parsed_event.json_body == {"message": "Hello from Lambda!"}
    assert parsed_event.method == raw_event["method"]
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.query_string_parameters == raw_event["queryStringParameters"]
    assert parsed_event.get_query_string_value("order-id") == "1"

    # DEPRECATED METHOD - Remove in V4
    with pytest.warns(PowertoolsDeprecationWarning):
        assert parsed_event.get_header_value("user_agent") == "curl/7.64.1"

    assert parsed_event.body == raw_event["body"]
    assert parsed_event.is_base64_encoded == raw_event["isBase64Encoded"]
    assert parsed_event.request_context.region == raw_event["requestContext"]["region"]
    assert parsed_event.request_context.service_network_arn == raw_event["requestContext"]["serviceNetworkArn"]
    assert parsed_event.request_context.service_arn == raw_event["requestContext"]["serviceArn"]
    assert parsed_event.request_context.target_group_arn == raw_event["requestContext"]["targetGroupArn"]
    assert parsed_event.request_context.time_epoch == raw_event["requestContext"]["timeEpoch"]
    assert (
        parsed_event.request_context.identity.source_vpc_arn == raw_event["requestContext"]["identity"]["sourceVpcArn"]
    )
    assert parsed_event.request_context.identity.get_type == raw_event["requestContext"]["identity"]["type"]
    assert parsed_event.request_context.identity.principal == raw_event["requestContext"]["identity"]["principal"]
    assert parsed_event.request_context.identity.session_name == raw_event["requestContext"]["identity"]["sessionName"]
    assert parsed_event.request_context.identity.x509_san_dns == raw_event["requestContext"]["identity"]["x509SanDns"]
    assert parsed_event.request_context.identity.x509_issuer_ou is None
    assert parsed_event.request_context.identity.x509_san_name_cn is None
    assert parsed_event.request_context.identity.x509_san_uri is None
    assert parsed_event.request_context.identity.x509_subject_cn is None
    assert parsed_event.request_context.identity.principal_org_id is None


def test_vpc_lattice_v2_event_with_query_string():
    # Event captured from a V2 target group: path carries the query string, which is also sent parsed
    raw_event = load_event("vpcLatticeV2EventWithQueryString.json")
    parsed_event = VPCLatticeEventV2(raw_event)

    assert parsed_event.path == "/echo"
    assert parsed_event.raw_event["path"] == "/echo?QS1=value1&QS1=value2&single=one"
    assert parsed_event.query_string_parameters == {"QS1": "value1,value2", "single": "one"}


@pytest.mark.parametrize(
    "event_path, expected_path",
    [
        ("/?query1=value1&query2=value2", "/"),
        ("/newpath?", "/newpath"),
        ("/newpath?next=/orders?page=2", "/newpath"),
        ("/files/report%3Fv2?download=true", "/files/report%3Fv2"),
    ],
    ids=["root_path", "empty_query", "question_mark_in_query", "encoded_question_mark_in_path"],
)
def test_vpc_lattice_v2_event_path_excludes_query_string(event_path, expected_path):
    raw_event = load_event("vpcLatticeV2Event.json")
    raw_event["path"] = event_path
    parsed_event = VPCLatticeEventV2(raw_event)

    assert parsed_event.path == expected_path
    assert parsed_event.raw_event["path"] == event_path


def test_vpc_lattice_v2_event_x509_identity():
    # GIVEN a VPC Lattice v2 event authenticated with IAM Roles Anywhere
    raw_event = load_event("vpcLatticeV2Event.json")
    raw_event["requestContext"]["identity"].update(
        {
            "x509IssuerOu": "IT Department",
            "x509SanDns": "example.com",
            "x509SanNameCn": "example-name",
            "x509SanUri": "https://example.com",
            "x509SubjectCn": "example-subject",
        },
    )

    # WHEN parsing the event
    identity = VPCLatticeEventV2(raw_event).request_context.identity

    # THEN all x509 fields are read from the event
    assert identity.x509_issuer_ou == "IT Department"
    assert identity.x509_san_dns == "example.com"
    assert identity.x509_san_name_cn == "example-name"
    assert identity.x509_san_uri == "https://example.com"
    assert identity.x509_subject_cn == "example-subject"
