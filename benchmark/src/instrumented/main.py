from aws_lambda_powertools import (Logger, Metrics, Tracer)


# Initialize core utilities
logger = Logger()
metrics = Metrics()
tracer = Tracer()


# Instrument Lambda function
@logger.inject_lambda_context
@metrics.log_metrics
@tracer.capture_lambda_handler
def handler(event, context):
    return {
        "message": "success"
    }