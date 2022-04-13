from aws_lambda_powertools import Tracer

tracer = Tracer()


@tracer.capture_method(capture_response=False)
def fetch_sensitive_information():
    return "sensitive_information"


@tracer.capture_lambda_handler(capture_response=False)
def handler(event, context):
    sensitive_information = fetch_sensitive_information()
