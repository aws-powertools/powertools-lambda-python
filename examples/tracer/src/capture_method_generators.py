from collections.abc import Generator

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


@tracer.capture_method
def collect_payment(charge_id: str) -> Generator[str, None, None]:
    yield f"dummy payment collected for charge: {charge_id}"


@tracer.capture_lambda_handler
def handler(event: dict, context: LambdaContext) -> str:
    charge_id = event.get("charge_id", "")
    return next(collect_payment(charge_id=charge_id))
