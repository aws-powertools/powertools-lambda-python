import asyncio
import os

import aiohttp

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.tracing import aiohttp_trace_config
from aws_lambda_powertools.utilities.typing import LambdaContext

ENDPOINT = os.getenv("PAYMENT_API", "")

tracer = Tracer()


@tracer.capture_method
async def collect_payment(charge_id: str) -> dict:
    async with aiohttp.ClientSession(trace_configs=[aiohttp_trace_config()]) as session:
        async with session.get(f"{ENDPOINT}/collect") as resp:
            return await resp.json()


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    charge_id = event.get("charge_id", "")
    return asyncio.run(collect_payment(charge_id=charge_id))
