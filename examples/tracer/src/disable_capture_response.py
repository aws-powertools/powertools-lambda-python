from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()


@tracer.capture_method(capture_response=False)
def collect_payment(charge_id: str) -> str:
    tracer.put_annotation(key="PaymentId", value=charge_id)
    logger.debug("Returning sensitive information....")
    return f"dummy payment collected for charge: {charge_id}"


@tracer.capture_lambda_handler(capture_response=False)
def lambda_handler(event: dict, context: LambdaContext) -> str:
    charge_id = event.get("charge_id", "")
    return collect_payment(charge_id=charge_id)
