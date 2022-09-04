from uuid import uuid4

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


@tracer.capture_method
def get_todos():
    return [{"id": f"{uuid4()}", "completed": False} for _ in range(5)]


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext):
    return get_todos()
