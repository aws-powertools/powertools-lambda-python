from __future__ import annotations

import base64
from typing import Any, Callable, Dict, List

import botocore
from aws_encryption_sdk import (
    CachingCryptoMaterialsManager,
    EncryptionSDKClient,
    LocalCryptoMaterialsCache,
    StrictAwsKmsMasterKeyProvider,
)

from aws_lambda_powertools.shared.user_agent import register_feature_to_botocore_session
from aws_lambda_powertools.utilities._data_masking.constants import (
    CACHE_CAPACITY,
    MAX_CACHE_AGE_SECONDS,
    MAX_MESSAGES_ENCRYPTED,
)
from aws_lambda_powertools.utilities._data_masking.provider import BaseProvider


class ContextMismatchError(Exception):
    def __init__(self, key):
        super().__init__(f"Encryption Context does not match expected value for key: {key}")
        self.key = key


class AwsEncryptionSdkProvider(BaseProvider):
    """
    The AwsEncryptionSdkProvider is used as a provider for the DataMasking class.

    This provider allows you to perform data masking using the AWS Encryption SDK
    for encryption and decryption. It integrates with the DataMasking class to
    securely encrypt and decrypt sensitive data.

    Usage Example:
    ```
    from aws_lambda_powertools.utilities.data_masking import DataMasking
    from aws_lambda_powertools.utilities.data_masking.providers.kms.aws_encryption_sdk import (
        AwsEncryptionSdkProvider,
    )


    def lambda_handler(event, context):
        provider = AwsEncryptionSdkProvider(["arn:aws:kms:us-east-1:0123456789012:key/key-id"])
        masker = DataMasking(provider=provider)

        data = {
            "project": "powertools",
            "sensitive": "xxxxxxxxxx"
        }

        masked = masker.encrypt(data,fields=["sensitive"])

        return masked

    ```
    """

    def __init__(
        self,
        keys: List[str],
        key_provider=None,
        local_cache_capacity: int = CACHE_CAPACITY,
        max_cache_age_seconds: float = MAX_CACHE_AGE_SECONDS,
        max_messages_encrypted: int = MAX_MESSAGES_ENCRYPTED,
        json_serializer: Callable | None = None,
        json_deserializer: Callable | None = None,
    ):
        super().__init__(json_serializer=json_serializer, json_deserializer=json_deserializer)

        self._key_provider = key_provider or KMSKeyProvider(
            keys=keys,
            local_cache_capacity=local_cache_capacity,
            max_cache_age_seconds=max_cache_age_seconds,
            max_messages_encrypted=max_messages_encrypted,
            json_serializer=self.json_serializer,
            json_deserializer=self.json_deserializer,
        )

    def encrypt(self, data: bytes | str | Dict | int, **provider_options) -> str:
        return self._key_provider.encrypt(data=data, **provider_options)

    def decrypt(self, data: str, **provider_options) -> Any:
        return self._key_provider.decrypt(data=data, **provider_options)


class KMSKeyProvider:

    """
    The KMSKeyProvider is responsible for assembling an AWS Key Management Service (KMS)
    client, a caching mechanism, and a keyring for secure key management and data encryption.
    """

    def __init__(
        self,
        keys: List[str],
        json_serializer: Callable,
        json_deserializer: Callable,
        local_cache_capacity: int = CACHE_CAPACITY,
        max_cache_age_seconds: float = MAX_CACHE_AGE_SECONDS,
        max_messages_encrypted: int = MAX_MESSAGES_ENCRYPTED,
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
        )

    def encrypt(self, data: bytes | str | Dict | float, **provider_options) -> str:
        """
        Encrypt data using the AwsEncryptionSdkProvider.

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
        data_encoded = self.json_serializer(data)
        ciphertext, _ = self.client.encrypt(
            source=data_encoded,
            materials_manager=self.cache_cmm,
            **provider_options,
        )
        ciphertext = base64.b64encode(ciphertext).decode()
        return ciphertext

    def decrypt(self, data: str, **provider_options) -> Any:
        """
        Decrypt data using AwsEncryptionSdkProvider.

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
        ciphertext_decoded = base64.b64decode(data)

        expected_context = provider_options.pop("encryption_context", {})

        ciphertext, decryptor_header = self.client.decrypt(
            source=ciphertext_decoded,
            key_provider=self.key_provider,
            **provider_options,
        )

        for key, value in expected_context.items():
            if decryptor_header.encryption_context.get(key) != value:
                raise ContextMismatchError(key)

        ciphertext = self.json_deserializer(ciphertext)
        return ciphertext
