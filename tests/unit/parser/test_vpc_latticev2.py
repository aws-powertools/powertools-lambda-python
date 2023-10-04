import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, parse
from aws_lambda_powertools.utilities.parser.models import VpcLatticeV2Model
from tests.functional.utils import load_event
from tests.unit.parser.schemas import MyVpcLatticeBusiness


def test_vpc_lattice_v2_event_with_envelope():
    raw_event = load_event("vpcLatticeV2Event.json")
    raw_event["body"] = '{"username": "Stephen", "name": "Bawks"}'
    parsed_event: MyVpcLatticeBusiness = parse(
        event=raw_event,
        model=MyVpcLatticeBusiness,
        envelope=envelopes.VpcLatticeV2Envelope,
    )

    assert parsed_event.username == "Stephen"
    assert parsed_event.name == "Bawks"


def test_vpc_lattice_v2_event():
    raw_event = load_event("vpcLatticeV2Event.json")
    model = VpcLatticeV2Model(**raw_event)

    assert model.body == raw_event["body"]
    assert model.method == raw_event["method"]
    assert model.path == raw_event["path"]
    assert model.is_base64_encoded == raw_event["isBase64Encoded"]
    assert model.headers == raw_event["headers"]
    assert model.query_string_parameters == raw_event["queryStringParameters"]
    assert model.request_context.region == raw_event["requestContext"]["region"]
    assert model.request_context.service_network_arn == raw_event["requestContext"]["serviceNetworkArn"]
    assert model.request_context.service_arn == raw_event["requestContext"]["serviceArn"]
    assert model.request_context.target_group_arn == raw_event["requestContext"]["targetGroupArn"]
    convert_time = int((model.request_context.time_epoch.timestamp() * 1000))
    event_converted_time = round(int(raw_event["requestContext"]["timeEpoch"]) / 1000)
    assert convert_time == event_converted_time
    assert model.request_context.identity.source_vpc_arn == raw_event["requestContext"]["identity"]["sourceVpcArn"]
    assert model.request_context.identity.get_type == raw_event["requestContext"]["identity"]["type"]
    assert model.request_context.identity.principal == raw_event["requestContext"]["identity"]["principal"]
    assert model.request_context.identity.session_name == raw_event["requestContext"]["identity"]["sessionName"]
    assert model.request_context.identity.x509_san_dns == raw_event["requestContext"]["identity"]["x509SanDns"]
    assert model.request_context.identity.x509_issuer_ou is None
    assert model.request_context.identity.x509_san_name_cn is None
    assert model.request_context.identity.x509_san_uri is None
    assert model.request_context.identity.x509_subject_cn is None
    assert model.request_context.identity.principal_org_id is None


def test_vpc_lattice_v2_event_custom_model():
    class MyCustomResource(VpcLatticeV2Model):
        body: str

    raw_event = load_event("vpcLatticeV2Event.json")
    model = MyCustomResource(**raw_event)

    assert model.body == raw_event["body"]


def test_vpc_lattice_v2_event_invalid():
    raw_event = load_event("vpcLatticeV2Event.json")
    raw_event["body"] = ["some_more_data"]

    with pytest.raises(ValidationError):
        VpcLatticeV2Model(**raw_event)
