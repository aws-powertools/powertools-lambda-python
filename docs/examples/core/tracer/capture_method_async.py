import asyncio
import contextlib

from aws_lambda_powertools import Tracer

tracer = Tracer()


@tracer.capture_method
async def collect_payment():
    ...
