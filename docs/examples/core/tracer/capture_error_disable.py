from aws_lambda_powertools import Tracer

tracer = Tracer()


@tracer.capture_lambda_handler(capture_error=False)
def handler(event, context):
    raise ValueError("some sensitive info in the stack trace...")
