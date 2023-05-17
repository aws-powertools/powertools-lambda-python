import base64
from typing import Any, Optional, Union

import botocore
from aws_encryption_sdk import (
    CachingCryptoMaterialsManager,
    EncryptionSDKClient,
    LocalCryptoMaterialsCache,
    StrictAwsKmsMasterKeyProvider,
)

from aws_lambda_powertools.utilities.data_masking.provider import Provider


class SingletonMeta(type):
    """Metaclass to cache class instances to optimize encryption"""

    _instances: dict["EncryptionManager", Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class AwsEncryptionSdkProvider(Provider, metaclass=SingletonMeta):
    CACHE_CAPACITY: int = 100
    MAX_ENTRY_AGE_SECONDS: float = 300.0
    MAX_MESSAGES: int = 200
    # NOTE: You can also set max messages/bytes per data key

    cache = LocalCryptoMaterialsCache(CACHE_CAPACITY)
    session = botocore.session.Session()

    def __init__(self, keys: list[str], client: Optional[EncryptionSDKClient()] = None) -> None:
        self.client = client or EncryptionSDKClient()
        self.keys = keys
        self.key_provider = StrictAwsKmsMasterKeyProvider(key_ids=self.keys, botocore_session=self.session)
        self.cache_cmm = CachingCryptoMaterialsManager(
            master_key_provider=self.key_provider,
            cache=self.cache,
            max_age=self.MAX_ENTRY_AGE_SECONDS,
            max_messages_encrypted=self.MAX_MESSAGES,
        )
        self.encryption_context = None

    def encrypt(self, data: Union[bytes, str], context: Optional[dict] = None, **kwargs) -> str:
        ciphertext, header = self.client.encrypt(
            source=data, encryption_context=context, materials_manager=self.cache_cmm, **kwargs
        )
        ciphertext = base64.b64encode(ciphertext).decode()
        self.encryption_context = header.encryption_context
        return ciphertext

    def decrypt(self, data: str, **kwargs) -> bytes:
        ciphertext_decoded = base64.b64decode(data)
        ciphertext, decrypted_header = self.client.decrypt(
            source=ciphertext_decoded, key_provider=self.key_provider, **kwargs
        )

        if self.encryption_context != decrypted_header.encryption_context:
            raise ValueError("Encryption context mismatch")
        return ciphertext
