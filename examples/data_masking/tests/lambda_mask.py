from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities.data_masking import DataMasking

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

data_masker = DataMasking()


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    data = event

    erased = data_masker.erase(data, fields=["testkey"])

    return erased
