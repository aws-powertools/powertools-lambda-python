from aws_lambda_powertools.utilities.data_classes.vpc_lattice import VPCLatticeEvent
from tests.functional.utils import load_event


def test_vpc_lattice_event():
    raw_event = load_event("vpcLatticeEvent.json")
    parsed_event = VPCLatticeEvent(raw_event)

    assert parsed_event.raw_path == raw_event["raw_path"]
    assert parsed_event.get_query_string_value("order-id") == "1"
    assert parsed_event.get_header_value("user_agent") == "curl/7.64.1"
    assert parsed_event.decoded_body == '{"test": "event"}'
    assert parsed_event.json_body == {"test": "event"}
    assert parsed_event.method == raw_event["method"]
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.query_string_parameters == raw_event["query_string_parameters"]
    assert parsed_event.body == raw_event["body"]
    assert parsed_event.is_base64_encoded == raw_event["is_base64_encoded"]
