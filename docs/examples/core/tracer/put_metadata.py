from aws_lambda_powertools import Tracer

tracer = Tracer()


@tracer.capture_lambda_handler
def handler(event, context):
    ...
    ret = some_logic()
    tracer.put_metadata(key="payment_response", value=ret)
