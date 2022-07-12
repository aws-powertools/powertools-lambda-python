import os

import requests

from aws_lambda_powertools import Logger

ENDPOINT = os.getenv("PAYMENT_API", "")
logger = Logger(service="payment")


class PaymentError(Exception):
    ...


def handler(event, context):
    logger.append_keys(payment_id="123456789")
    charge_id = event.get("charge_id", "")

    try:
        ret = requests.post(url=f"{ENDPOINT}/collect", data={"charge_id": charge_id})
        ret.raise_for_status()

        logger.info("Charge collected successfully", extra={"charge_id": charge_id})
        return ret.json()
    except requests.HTTPError as e:
        raise PaymentError(f"Unable to collect payment for charge {charge_id}") from e

    logger.info("goodbye")
