import asyncio

from aws_lambda_powertools import Tracer

tracer = Tracer()


async def another_async_task():
    async with tracer.provider.in_subsegment_async("## another_async_task") as subsegment:
        subsegment.put_annotation(key="key", value="value")
        subsegment.put_metadata(key="key", value="value", namespace="namespace")
        ...


async def another_async_task_2():
    ...


@tracer.capture_method
async def collect_payment(charge_id):
    asyncio.gather(another_async_task(), another_async_task_2())
    ...
