import base64
from typing import Any, Dict, List, Optional, Union

import botocore
from aws_encryption_sdk import (
    CachingCryptoMaterialsManager,
    EncryptionSDKClient,
    LocalCryptoMaterialsCache,
    StrictAwsKmsMasterKeyProvider,
)

from aws_lambda_powertools.shared.user_agent import register_feature_to_botocore_session
from aws_lambda_powertools.utilities.data_masking.provider import BaseProvider


class ContextMismatchError(Exception):
    def __init__(self, key):
        super().__init__(f"Encryption Context does not match expected value for key: {key}")
        self.key = key


class Singleton:
    _instances: Dict[Any, "AwsEncryptionSdkProvider"] = {}

    def __new__(cls, *args, **kwargs):
        # Generate a unique key based on the configuration
        # Create a tuple by iterating through the values in kwargs, sorting them,
        # and then adding them to the tuple.
        config_key = tuple(v for value in kwargs.values() for v in sorted(value))

        if config_key not in cls._instances:
            cls._instances[config_key] = super(Singleton, cls).__new__(cls, *args)
            print("in if class instances:", cls._instances)
        return cls._instances[config_key]


CACHE_CAPACITY: int = 100
MAX_CACHE_AGE_SECONDS: float = 300.0
MAX_MESSAGES_ENCRYPTED: int = 200
# NOTE: You can also set max messages/bytes per data key


class AwsEncryptionSdkProvider(BaseProvider, Singleton):
    """
    The AwsEncryptionSdkProvider is to be used as a Provider for the Datamasking class.

    Example
    -------
        >>> data_masker = DataMasking(provider=AwsEncryptionSdkProvider(keys=[keyARN1, keyARN2,...,]))
        >>> encrypted_data = data_masker.encrypt("a string")
        "encrptedBase64String"
        >>> decrypted_data = data_masker.decrypt(encrypted_data)
        "a string"
    """

    session = botocore.session.Session()
    register_feature_to_botocore_session(session, "data-masking")

    def __init__(
        self,
        keys: List[str],
        client: Optional[EncryptionSDKClient] = None,
        local_cache_capacity: Optional[int] = CACHE_CAPACITY,
        max_cache_age_seconds: Optional[float] = MAX_CACHE_AGE_SECONDS,
        max_messages_encrypted: Optional[int] = MAX_MESSAGES_ENCRYPTED,
    ):
        self.client = client or EncryptionSDKClient()
        self.keys = keys
        self.cache = LocalCryptoMaterialsCache(local_cache_capacity)
        self.key_provider = StrictAwsKmsMasterKeyProvider(key_ids=self.keys, botocore_session=self.session)
        self.cache_cmm = CachingCryptoMaterialsManager(
            master_key_provider=self.key_provider,
            cache=self.cache,
            max_age=max_cache_age_seconds,
            max_messages_encrypted=max_messages_encrypted,
        )

    def _serialize(self, data: Any):
        return bytes(str(data), "utf-8")

    def _deserialize(self, data: bytes):
        return data.decode("utf-8")

    def encrypt(self, data: Union[bytes, str], **provider_options) -> str:
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
        data = self._serialize(data)
        ciphertext, _ = self.client.encrypt(source=data, materials_manager=self.cache_cmm, **provider_options)
        ciphertext = base64.b64encode(ciphertext).decode()
        return ciphertext

    def decrypt(self, data: str, **provider_options) -> bytes:
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

        ciphertext = self._deserialize(ciphertext)
        return ciphertext
