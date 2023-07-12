from aws_lambda_powertools.utilities.jmespath_utils import extract_data_from_envelope
from aws_lambda_powertools.utilities.typing import LambdaContext


def handler(event: dict, context: LambdaContext) -> dict:
    payload = extract_data_from_envelope(data=event, envelope="powertools_json(body)")
    customer_id = payload.get("customerId")  # now deserialized

    # also works for fetching and flattening deeply nested data
    some_data = extract_data_from_envelope(data=event, envelope="deeply_nested[*].some_data[]")

    return {"customer_id": customer_id, "message": "success", "context": some_data, "statusCode": 200}
