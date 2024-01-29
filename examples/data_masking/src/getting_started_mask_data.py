from __future__ import annotations

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_masking import DataMasking
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
data_masker = DataMasking()


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    data: dict = event.get("body", {})

    logger.info("Erasing fields email, address.street, and company_address")

    erased = data_masker.erase(data, fields=["email", "address.street", "company_address"])  # (1)!

    return erased
