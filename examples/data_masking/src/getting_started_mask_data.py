from typing import Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities._data_masking import DataMasking
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
data_masker = DataMasking()


def lambda_handler(event: dict, context: LambdaContext) -> Dict:
    data = event.get("body")

    logger.info("Masking fields email, address.street, and company_address")

    masked = data_masker.mask(data=data, fields=["email", "address.street", "company_address"])

    return {"payload_masked": masked}
