from aws_lambda_powertools import Tracer

tracer = Tracer(service="payment")


@tracer.capture_method
def collect_payment(charge_id: str):
    ...
