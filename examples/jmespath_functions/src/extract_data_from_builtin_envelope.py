from aws_lambda_powertools.utilities.jmespath_utils import envelopes, extract_data_from_envelope
from aws_lambda_powertools.utilities.typing import LambdaContext


def handler(event: dict, context: LambdaContext) -> dict:
    payload = extract_data_from_envelope(data=event, envelope=envelopes.SQS)
    customer_id = payload.get("customerId")  # now deserialized

    return {"customer_id": customer_id, "message": "success", "statusCode": 200}
