import os
from typing import Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities._data_masking import DataMasking
from aws_lambda_powertools.utilities._data_masking.provider.kms.aws_encryption_sdk import AWSEncryptionSDKProvider
from aws_lambda_powertools.utilities.typing import LambdaContext

KMS_KEY_ARN = os.getenv("KMS_KEY_ARN", "")

encryption_provider = AWSEncryptionSDKProvider(keys=[KMS_KEY_ARN])
data_masker = DataMasking(provider=encryption_provider)

logger = Logger()


@logger.inject_lambda_context
def lambda_handler(event: Dict, context: LambdaContext) -> Dict:
    data = event.get("body", {})

    logger.info("Decrypting email field")

    decrypted: dict = data_masker.encrypt(
        data,
        fields=["email"],
        tenant_id=event.get("tenant_id", ""),  # (1)!
    )

    return decrypted
