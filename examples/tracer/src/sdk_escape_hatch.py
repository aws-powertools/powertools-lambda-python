from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


def collect_payment(charge_id: str) -> str:
    return f"dummy payment collected for charge: {charge_id}"


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> str:
    charge_id = event.get("charge_id", "")
    with tracer.provider.in_subsegment("## collect_payment") as subsegment:
        subsegment.put_annotation(key="PaymentId", value=charge_id)
        ret = collect_payment(charge_id=charge_id)
        subsegment.put_metadata(key="payment_response", value=ret)

    return ret
