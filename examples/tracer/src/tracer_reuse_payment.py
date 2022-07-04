from aws_lambda_powertools import Tracer

tracer = Tracer()


@tracer.capture_method
def collect_payment(charge_id: str) -> str:
    return f"dummy payment collected for charge: {charge_id}"
