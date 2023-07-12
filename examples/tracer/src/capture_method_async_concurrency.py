import asyncio

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


async def another_async_task():
    async with tracer.provider.in_subsegment_async("## another_async_task") as subsegment:
        subsegment.put_annotation(key="key", value="value")
        subsegment.put_metadata(key="key", value="value", namespace="namespace")
        ...


async def another_async_task_2():
    async with tracer.provider.in_subsegment_async("## another_async_task_2") as subsegment:
        subsegment.put_annotation(key="key", value="value")
        subsegment.put_metadata(key="key", value="value", namespace="namespace")
        ...


async def collect_payment(charge_id: str) -> str:
    await asyncio.gather(another_async_task(), another_async_task_2())
    return f"dummy payment collected for charge: {charge_id}"


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> str:
    charge_id = event.get("charge_id", "")
    return asyncio.run(collect_payment(charge_id=charge_id))
