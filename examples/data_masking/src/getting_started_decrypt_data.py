import os
from typing import Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities._data_masking import DataMasking
from aws_lambda_powertools.utilities._data_masking.provider.kms.aws_encryption_sdk import AwsEncryptionSdkProvider
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

KMS_KEY_ARN: str = os.getenv("KMS_KEY_ARN", "")
encryption_provider = AwsEncryptionSdkProvider(keys=[KMS_KEY_ARN])
data_masker = DataMasking(provider=encryption_provider)


def lambda_handler(event: Dict, context: LambdaContext) -> Dict:
    data = event.get("body")

    logger.info("Encrypting fields email, address.street, and company_address")

    encrypted = data_masker.encrypt(data=data, fields=["email", "address.street", "company_address"])

    return {"payload_encrypted": encrypted}
