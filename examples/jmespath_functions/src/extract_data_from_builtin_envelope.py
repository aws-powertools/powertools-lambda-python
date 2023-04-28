from __future__ import annotations

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.jmespath_utils import (
    envelopes,
    extract_data_from_envelope,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def handler(event: dict, context: LambdaContext) -> dict:
    records: list = extract_data_from_envelope(data=event, envelope=envelopes.SQS)
    for record in records:  # records is a list
        logger.info(record.get("customerId"))  # now deserialized

    return {"message": "success", "statusCode": 200}
