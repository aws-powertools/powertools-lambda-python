from tracer_reuse_module import collect_payment

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


@tracer.capture_lambda_handler
def handler(event: dict, context: LambdaContext) -> str:
    charge_id = event.get("charge_id", "")
    return collect_payment(charge_id=charge_id)
