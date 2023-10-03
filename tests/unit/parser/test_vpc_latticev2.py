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
    assert model.query_string_parameters == raw_event["query_string_parameters"]
    assert model.request_context == raw_event["requestContext"]


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
