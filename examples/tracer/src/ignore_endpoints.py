import os

import requests

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

ENDPOINT = os.getenv("PAYMENT_API", "")
IGNORE_URLS = ["/collect", "/refund"]

tracer = Tracer()
tracer.ignore_endpoint(hostname=ENDPOINT, urls=IGNORE_URLS)
tracer.ignore_endpoint(hostname=f"*.{ENDPOINT}", urls=IGNORE_URLS)  # `<stage>.ENDPOINT`


class PaymentError(Exception):
    ...


@tracer.capture_method(capture_error=False)
def collect_payment(charge_id: str) -> dict:
    try:
        ret = requests.post(url=f"{ENDPOINT}/collect", data={"charge_id": charge_id})
        ret.raise_for_status()
        return ret.json()
    except requests.HTTPError as e:
        raise PaymentError(f"Unable to collect payment for charge {charge_id}") from e


@tracer.capture_lambda_handler(capture_error=False)
def lambda_handler(event: dict, context: LambdaContext) -> str:
    charge_id = event.get("charge_id", "")
    ret = collect_payment(charge_id=charge_id)

    return ret.get("receipt_id", "")
