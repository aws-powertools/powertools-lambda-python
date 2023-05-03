from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()  # Sets service via POWERTOOLS_SERVICE_NAME env var
# OR tracer = Tracer(service="example")


def collect_payment(charge_id: str) -> str:
    return f"dummy payment collected for charge: {charge_id}"


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> str:
    charge_id = event.get("charge_id", "")
    return collect_payment(charge_id=charge_id)
