import asyncio

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


@tracer.capture_method
async def collect_payment(charge_id: str) -> str:
    tracer.put_annotation(key="PaymentId", value=charge_id)
    await asyncio.sleep(0.5)
    return f"dummy payment collected for charge: {charge_id}"


@tracer.capture_lambda_handler
def handler(event: dict, context: LambdaContext) -> str:
    charge_id = event.get("charge_id", "")
    return asyncio.run(collect_payment(charge_id=charge_id))
