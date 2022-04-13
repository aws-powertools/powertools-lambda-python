import asyncio

import aiohttp

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.tracing import aiohttp_trace_config

tracer = Tracer()


async def aiohttp_task():
    async with aiohttp.ClientSession(trace_configs=[aiohttp_trace_config()]) as session:
        async with session.get("https://httpbin.org/json") as resp:
            resp = await resp.json()
            return resp
