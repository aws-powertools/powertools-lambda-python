import asyncio
import contextlib

from aws_lambda_powertools import Tracer

tracer = Tracer()


@tracer.capture_method
def collect_payment_gen():
    yield result
    ...
