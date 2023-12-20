from __future__ import annotations

import os

import ujson

from aws_lambda_powertools.utilities._data_masking import DataMasking
from aws_lambda_powertools.utilities._data_masking.provider.kms.aws_encryption_sdk import (
    AWSEncryptionSDKProvider,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

KMS_KEY_ARN = os.getenv("KMS_KEY_ARN", "")

encryption_provider = AWSEncryptionSDKProvider(
    keys=[KMS_KEY_ARN],
    json_serializer=ujson.dumps,
    json_deserializer=ujson.loads,
)
data_masker = DataMasking(provider=encryption_provider)


def lambda_handler(event: dict, context: LambdaContext) -> str:
    data: dict = event.get("body", {})

    return data_masker.encrypt(data)
