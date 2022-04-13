import asyncio
import contextlib

from aws_lambda_powertools import Tracer

tracer = Tracer()


@contextlib.contextmanager
@tracer.capture_method
def collect_payment_ctxman():
    yield result
    ...
