from aws_lambda_powertools.utilities.data_classes.vpc_lattice import VPCLatticeEvent
from tests.functional.utils import load_event


def test_vpc_lattice_event():
    event = VPCLatticeEvent(load_event("vpcLatticeEvent.json"))

    assert event.raw_path == event["raw_path"]
    assert event.get_query_string_value("order-id") == "1"
    assert event.get_header_value("user_agent") == "curl/7.64.1"
    assert event.decoded_body == '{"test": "event"}'
    assert event.json_body == {"test": "event"}
    assert event.method == event["method"]
    assert event.headers == event["headers"]
    assert event.query_string_parameters == event["query_string_parameters"]
    assert event.body == event["body"]
    assert event.is_base64_encoded == event["is_base64_encoded"]
