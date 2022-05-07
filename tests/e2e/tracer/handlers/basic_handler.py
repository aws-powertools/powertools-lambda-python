import os

from aws_lambda_powertools import Tracer

tracer = Tracer()
tracer = Tracer(service="e2e-tests-app")

ANNOTATION_KEY = os.environ["ANNOTATION_KEY"]
ANNOTATION_VALUE = os.environ["ANNOTATION_VALUE"]


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    tracer.put_annotation(key=ANNOTATION_KEY, value=ANNOTATION_VALUE)
    tracer.put_metadata(key=ANNOTATION_KEY, value=ANNOTATION_VALUE)
    return "success"
