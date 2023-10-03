import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, parse
from aws_lambda_powertools.utilities.parser.models import VpcLatticeModel, VpcLatticeV2Model
from tests.functional.utils import load_event
from tests.unit.parser.schemas import MyVpcLatticeBusiness


def test_vpc_lattice_event_with_envelope():
    raw_event = load_event("vpcLatticeEvent.json")
    raw_event["body"] = '{"username": "Leandro", "name": "Damascena"}'
    parsed_event: MyVpcLatticeBusiness = parse(
        event=raw_event,
        model=MyVpcLatticeBusiness,
        envelope=envelopes.VpcLatticeEnvelope,
    )

    assert parsed_event.username == "Leandro"
    assert parsed_event.name == "Damascena"


def test_vpc_lattice_event():
    raw_event = load_event("vpcLatticeEvent.json")
    model = VpcLatticeModel(**raw_event)

    assert model.body == raw_event["body"]
    assert model.method == raw_event["method"]
    assert model.raw_path == raw_event["raw_path"]
    assert model.is_base64_encoded == raw_event["is_base64_encoded"]
    assert model.headers == raw_event["headers"]
    assert model.query_string_parameters == raw_event["query_string_parameters"]


def test_vpc_lattice_event_custom_model():
    class MyCustomResource(VpcLatticeModel):
        body: str

    raw_event = load_event("vpcLatticeEvent.json")
    model = MyCustomResource(**raw_event)

    assert model.body == raw_event["body"]


def test_vpc_lattice_event_invalid():
    raw_event = load_event("vpcLatticeEvent.json")
    raw_event["body"] = ["some_data"]

    with pytest.raises(ValidationError):
        VpcLatticeModel(**raw_event)


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
    assert model.is_base64_encoded == raw_event["is_base64_encoded"]
    assert model.headers == raw_event["headers"]
    assert model.query_string_parameters == raw_event["query_string_parameters"]
    assert model.request_context == raw_event["request_context"]

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
