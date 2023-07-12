import contextlib
from collections.abc import Generator

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()


@contextlib.contextmanager
@tracer.capture_method
def collect_payment(charge_id: str) -> Generator[str, None, None]:
    try:
        yield f"dummy payment collected for charge: {charge_id}"
    finally:
        tracer.put_annotation(key="PaymentId", value=charge_id)


@tracer.capture_lambda_handler
@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> str:
    charge_id = event.get("charge_id", "")
    with collect_payment(charge_id=charge_id) as receipt_id:
        logger.info(f"Processing payment collection for charge {charge_id} with receipt {receipt_id}")

    return receipt_id
