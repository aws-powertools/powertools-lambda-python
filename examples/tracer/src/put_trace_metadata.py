from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


def collect_payment(charge_id: str) -> str:
    return f"dummy payment collected for charge: {charge_id}"


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> str:
    payment_context = {
        "charge_id": event.get("charge_id", ""),
        "merchant_id": event.get("merchant_id", ""),
        "request_id": context.aws_request_id,
    }
    payment_context["receipt_id"] = collect_payment(charge_id=payment_context["charge_id"])
    tracer.put_metadata(key="payment_response", value=payment_context)

    return payment_context["receipt_id"]
