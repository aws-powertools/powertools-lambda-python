from __future__ import annotations

import os
from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_masking import DataMasking
from aws_lambda_powertools.utilities.data_masking.provider.kms.aws_encryption_sdk import AWSEncryptionSDKProvider

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

KMS_KEY_ARN = os.getenv("KMS_KEY_ARN", "")

encryption_provider = AWSEncryptionSDKProvider(keys=[KMS_KEY_ARN])
data_masker = DataMasking(provider=encryption_provider)

logger = Logger()


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    data = event.get("body", {})

    logger.info("Decrypting whole object")

    decrypted: dict = data_masker.decrypt(
        data,
        data_classification="confidential",  # (1)!
        data_type="customer-data",
        tenant_id="a06bf973-0734-4b53-9072-39d7ac5b2cba",
    )

    return decrypted
