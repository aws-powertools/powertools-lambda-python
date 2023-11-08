from __future__ import annotations

import base64
from typing import Any, Callable, Dict, Union

from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from aws_lambda_powertools.utilities.data_masking.provider import BaseProvider
from aws_lambda_powertools.utilities.data_masking.provider.kms.aws_encryption_sdk import AwsEncryptionSdkProvider


class FakeEncryptionKeyProvider(BaseProvider):
    def __init__(
        self,
        json_serializer: Callable[[Dict], str] | None = None,
        json_deserializer: Callable[[Union[Dict, str, bool, int, float]], str] | None = None,
    ):
        super().__init__(json_serializer=json_serializer, json_deserializer=json_deserializer)

    def encrypt(self, data: bytes | str, **kwargs) -> str:
        data = self.json_serializer(data)
        ciphertext = base64.b64encode(data).decode()
        return ciphertext

    def decrypt(self, data: bytes, **kwargs) -> Any:
        ciphertext_decoded = base64.b64decode(data)
        ciphertext = self.json_deserializer(ciphertext_decoded)
        return ciphertext


def handler(event, context):
    data = "mock_value"

    fake_key_provider = FakeEncryptionKeyProvider()
    provider = AwsEncryptionSdkProvider(
        keys=["dummy"],
        key_provider=fake_key_provider,
    )
    data_masker = DataMasking(provider=provider)

    encrypted = data_masker.encrypt(data=data)
    data_masker.decrypt(data=encrypted)

    return {"message": "mock_value"}
