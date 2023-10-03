from aws_lambda_powertools.utilities.data_classes.vpc_lattice import VPCLatticeEventV2
from tests.functional.utils import load_event


def test_vpc_lattice_event():
    raw_event = load_event("vpcLatticeV2Event.json")
    parsed_event = VPCLatticeEventV2(raw_event)

    assert parsed_event.path == raw_event["path"]
    assert parsed_event.get_query_string_value("order-id") == "1"
    assert parsed_event.get_header_value("user_agent") == "curl/7.64.1"
    assert parsed_event.decoded_body == '{"message": "Hello from Lambda!"}'
    assert parsed_event.json_body == {"message": "Hello from Lambda!"}
    assert parsed_event.method == raw_event["method"]
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.query_string_parameters == raw_event["query_string_parameters"]
    assert parsed_event.body == raw_event["body"]
    assert parsed_event.is_base64_encoded == raw_event["isBase64Encoded"]
    assert parsed_event.request_context.region == raw_event["requestContext"]["region"]
    assert parsed_event.request_context.service_network_arn == raw_event["requestContext"]["serviceNetworkArn"]
    assert parsed_event.request_context.service_arn == raw_event["requestContext"]["serviceArn"]
    assert parsed_event.request_context.target_group_arn == raw_event["requestContext"]["targetGroupArn"]
    assert parsed_event.request_context.source_vpc_arn == raw_event["requestContext"]["identity"]["sourceVpcArn"]
    assert parsed_event.request_context.time_epoch == raw_event["requestContext"]["timeEpoch"]
