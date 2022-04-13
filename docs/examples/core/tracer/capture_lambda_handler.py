from aws_lambda_powertools import Tracer

tracer = Tracer()  # Sets service via env var
# OR tracer = Tracer(service="example")


@tracer.capture_lambda_handler
def handler(event, context):
    charge_id = event.get("charge_id")
    payment = collect_payment(charge_id)
    ...
