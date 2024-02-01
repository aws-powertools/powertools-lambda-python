from __future__ import annotations

import os

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.data_masking import DataMasking
from aws_lambda_powertools.utilities.data_masking.provider.kms.aws_encryption_sdk import AWSEncryptionSDKProvider
from aws_lambda_powertools.utilities.typing import LambdaContext

KMS_KEY_ARN = os.getenv("KMS_KEY_ARN", "")

tracer = Tracer()
logger = Logger()


@tracer.capture_lambda_handler
@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info("Hello world function - HTTP 200")

    data = event["body"]

    data_masker = DataMasking(provider=AWSEncryptionSDKProvider(keys=[KMS_KEY_ARN]))
    encrypted = data_masker.encrypt(data)
    decrypted = data_masker.decrypt(encrypted)
    return {"Decrypted_json": decrypted}
