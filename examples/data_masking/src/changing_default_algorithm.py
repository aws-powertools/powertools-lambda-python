from __future__ import annotations

import os

from aws_encryption_sdk.identifiers import Algorithm

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_masking import DataMasking
from aws_lambda_powertools.utilities.data_masking.provider.kms.aws_encryption_sdk import AWSEncryptionSDKProvider
from aws_lambda_powertools.utilities.typing import LambdaContext

KMS_KEY_ARN = os.getenv("KMS_KEY_ARN", "")

encryption_provider = AWSEncryptionSDKProvider(keys=[KMS_KEY_ARN])
data_masker = DataMasking(provider=encryption_provider)

logger = Logger()


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> str:
    data: dict = event.get("body", {})

    logger.info("Encrypting whole object with a different algorithm")

    provider_options = {"algorithm": Algorithm.AES_256_GCM_HKDF_SHA512_COMMIT_KEY}

    encrypted = data_masker.encrypt(
        data,
        provider_options=provider_options,
    )

    return encrypted
