from aws_lambda_powertools import Tracer

tracer = Tracer()


@tracer.capture_lambda_handler
def handler(event, context):
    with tracer.provider.in_subsegment("## custom subsegment") as subsegment:
        ret = some_work()
        subsegment.put_metadata("response", ret)
