from __future__ import annotations

import base64
import functools
import json
import logging
from binascii import Error
from typing import Any, Callable, List

import botocore
from aws_encryption_sdk import (
    CachingCryptoMaterialsManager,
    EncryptionSDKClient,
    LocalCryptoMaterialsCache,
    StrictAwsKmsMasterKeyProvider,
)
from aws_encryption_sdk.exceptions import (
    DecryptKeyError,
    GenerateKeyError,
    NotSupportedError,
)

from aws_lambda_powertools.shared.user_agent import register_feature_to_botocore_session
from aws_lambda_powertools.utilities._data_masking.constants import (
    CACHE_CAPACITY,
    MAX_BYTES_ENCRYPTED,
    MAX_CACHE_AGE_SECONDS,
    MAX_MESSAGES_ENCRYPTED,
)
from aws_lambda_powertools.utilities._data_masking.exceptions import (
    DataMaskingContextMismatchError,
    DataMaskingDecryptKeyError,
    DataMaskingDecryptValueError,
    DataMaskingEncryptKeyError,
    DataMaskingUnsupportedTypeError,
)
from aws_lambda_powertools.utilities._data_masking.provider import BaseProvider

logger = logging.getLogger(__name__)


class AWSEncryptionSDKProvider(BaseProvider):
    """
    The AWSEncryptionSDKProvider is used as a provider for the DataMasking class.

    Usage
    -------
    ```
    from aws_lambda_powertools.utilities.data_masking import DataMasking
    from aws_lambda_powertools.utilities.data_masking.providers.kms.aws_encryption_sdk import (
        AWSEncryptionSDKProvider,
    )


    def lambda_handler(event, context):
        provider = AWSEncryptionSDKProvider(["arn:aws:kms:us-east-1:0123456789012:key/key-id"])
        data_masker = DataMasking(provider=provider)

        data = {
            "project": "powertools",
            "sensitive": "password"
        }

        encrypted = data_masker.encrypt(data, fields=["sensitive"])

        return encrypted

    ```
    """

    def __init__(
        self,
        keys: List[str],
        key_provider=None,
        local_cache_capacity: int = CACHE_CAPACITY,
        max_cache_age_seconds: float = MAX_CACHE_AGE_SECONDS,
        max_messages_encrypted: int = MAX_MESSAGES_ENCRYPTED,
        max_bytes_encrypted: int = MAX_BYTES_ENCRYPTED,
        json_serializer: Callable[..., str] = functools.partial(json.dumps, ensure_ascii=False),
        json_deserializer: Callable[[str], Any] = json.loads,
    ):
        super().__init__(json_serializer=json_serializer, json_deserializer=json_deserializer)

        self._key_provider = key_provider or KMSKeyProvider(
            keys=keys,
            local_cache_capacity=local_cache_capacity,
            max_cache_age_seconds=max_cache_age_seconds,
            max_messages_encrypted=max_messages_encrypted,
            max_bytes_encrypted=max_bytes_encrypted,
            json_serializer=json_serializer,
            json_deserializer=json_deserializer,
        )

    def encrypt(self, data: Any, provider_options: dict | None = None, **encryption_context: str) -> str:
        return self._key_provider.encrypt(data=data, provider_options=provider_options, **encryption_context)

    def decrypt(self, data: str, provider_options: dict | None = None, **encryption_context: str) -> Any:
        return self._key_provider.decrypt(data=data, provider_options=provider_options, **encryption_context)


class KMSKeyProvider:

    """
    The KMSKeyProvider is responsible for assembling an AWS Key Management Service (KMS)
    client, a caching mechanism, and a keyring for secure key management and data encryption.
    """

    def __init__(
        self,
        keys: List[str],
        json_serializer: Callable[..., str],
        json_deserializer: Callable[[str], Any],
        local_cache_capacity: int = CACHE_CAPACITY,
        max_cache_age_seconds: float = MAX_CACHE_AGE_SECONDS,
        max_messages_encrypted: int = MAX_MESSAGES_ENCRYPTED,
        max_bytes_encrypted: int = MAX_BYTES_ENCRYPTED,
    ):
        session = botocore.session.Session()
        register_feature_to_botocore_session(session, "data-masking")

        self.json_serializer = json_serializer
        self.json_deserializer = json_deserializer
        self.client = EncryptionSDKClient()
        self.keys = keys
        self.cache = LocalCryptoMaterialsCache(local_cache_capacity)
        self.key_provider = StrictAwsKmsMasterKeyProvider(key_ids=self.keys, botocore_session=session)
        self.cache_cmm = CachingCryptoMaterialsManager(
            master_key_provider=self.key_provider,
            cache=self.cache,
            max_age=max_cache_age_seconds,
            max_messages_encrypted=max_messages_encrypted,
            max_bytes_encrypted=max_bytes_encrypted,
        )

    def encrypt(self, data: Any, provider_options: dict | None = None, **encryption_context: str) -> str:
        """
        Encrypt data using the AWSEncryptionSDKProvider.

        Parameters
        -------
            data : Union[bytes, str]
                The data to be encrypted.
            provider_options
                Additional options for the aws_encryption_sdk.EncryptionSDKClient

        Returns
        -------
            ciphertext : str
                The encrypted data, as a base64-encoded string.
        """
        provider_options = provider_options or {}
        self._validate_encryption_context(encryption_context)

        data_encoded = self.json_serializer(data).encode("utf-8")
        try:
            ciphertext, _ = self.client.encrypt(
                source=data_encoded,
                materials_manager=self.cache_cmm,
                encryption_context=encryption_context,
                **provider_options,
            )
        except GenerateKeyError:
            raise DataMaskingEncryptKeyError(
                "Failed to encrypt data. Please ensure you are using a valid Symmetric AWS KMS Key ARN, not KMS Key ID or alias.",  # noqa E501
            )
        ciphertext = base64.b64encode(ciphertext).decode()
        return ciphertext

    def decrypt(self, data: str, provider_options: dict | None = None, **encryption_context: str) -> Any:
        """
        Decrypt data using AWSEncryptionSDKProvider.

        Parameters
        -------
            data : Union[bytes, str]
                The encrypted data, as a base64-encoded string
            provider_options
                Additional options for the aws_encryption_sdk.EncryptionSDKClient

        Returns
        -------
            ciphertext : bytes
                The decrypted data in bytes
        """
        provider_options = provider_options or {}
        self._validate_encryption_context(encryption_context)

        try:
            ciphertext_decoded = base64.b64decode(data)
        except Error:
            raise DataMaskingDecryptValueError(
                "Data decryption failed. Please ensure that you are attempting to decrypt data that was previously encrypted.",  # noqa E501
            )

        try:
            ciphertext, decryptor_header = self.client.decrypt(
                source=ciphertext_decoded,
                key_provider=self.key_provider,
                **provider_options,
            )
        except DecryptKeyError:
            raise DataMaskingDecryptKeyError(
                "Failed to decrypt data - Please ensure you are using a valid Symmetric AWS KMS Key ARN, not KMS Key ID or alias.",  # noqa E501
            )
        except (TypeError, NotSupportedError):
            raise DataMaskingDecryptValueError(
                "Data decryption failed. Please ensure that you are attempting to decrypt data that was previously encrypted.",  # noqa E501
            )

        self._compare_encryption_context(encryption_context, decryptor_header)

        ciphertext = self.json_deserializer(ciphertext.decode("utf-8"))
        return ciphertext

    @staticmethod
    def _validate_encryption_context(context: dict):
        if not context:
            return

        for key, value in context.items():
            if not isinstance(value, str):
                raise DataMaskingUnsupportedTypeError(
                    f"Encryption context values must be string. Received: {key}={value}",
                )

    @staticmethod
    def _compare_encryption_context(context: dict, decryptor_header):
        if not context:
            return

        for key, value in context.items():
            if decryptor_header.encryption_context.get(key) != value:
                raise DataMaskingContextMismatchError(
                    f"Encryption Context does not match expected value for key: {key}",
                )
