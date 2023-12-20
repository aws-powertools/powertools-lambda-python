from __future__ import annotations

from aws_lambda_powertools.utilities.data_masking import DataMasking
from aws_lambda_powertools.utilities.typing import LambdaContext

data_masker = DataMasking()


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    data = event

    masked = data_masker.mask(data, fields=["testkey"])

    return masked
