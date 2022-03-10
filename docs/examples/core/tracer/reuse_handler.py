from payment import collect_payment

from aws_lambda_powertools import Tracer

tracer = Tracer(service="payment")


@tracer.capture_lambda_handler
def handler(event, context):
    charge_id = event.get("charge_id")
    payment = collect_payment(charge_id)
