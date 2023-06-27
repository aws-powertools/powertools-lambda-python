import pytest

from aws_lambda_powertools.utilities.parser import (
    ValidationError,
    envelopes,
    event_parser,
)
from aws_lambda_powertools.utilities.parser.models import VpcLatticeModel
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyVpcLatticeBusiness
from tests.functional.utils import load_event


@event_parser(model=MyVpcLatticeBusiness, envelope=envelopes.VpcLatticeEnvelope)
def handle_lambda_vpclattice_with_envelope(event: MyVpcLatticeBusiness, context: LambdaContext):
    assert event.username == "Leandro"
    assert event.name == "Damascena"


def test_vpc_lattice_event_with_envelope():
    event = load_event("vpcLatticeEvent.json")
    event["body"] = '{"username": "Leandro", "name": "Damascena"}'
    handle_lambda_vpclattice_with_envelope(event, LambdaContext())


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
