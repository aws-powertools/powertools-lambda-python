import base64
from typing import Any, Dict, List, Optional, Union

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

    _instances: Dict["AwsEncryptionSdkProvider", Any] = {}

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

    def __init__(self, keys: List[str], client: Optional[EncryptionSDKClient] = None) -> None:
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

    def encrypt(self, data: Union[bytes, str], *args, **kwargs) -> str:
        context = kwargs["context"]
        ciphertext, header = self.client.encrypt(
            # Turn all data into string? bc we’re turning everything into a dict
            # in order to get the key values even if they pass in a json str of a dict
            source=str(data),
            encryption_context=context,
            materials_manager=self.cache_cmm,
            *args,
            **kwargs
        )
        ciphertext = base64.b64encode(ciphertext).decode()
        self.encryption_context = header.encryption_context
        return ciphertext

    def decrypt(self, data: str, *args, **kwargs) -> bytes:
        ciphertext_decoded = base64.b64decode(data)
        ciphertext, decrypted_header = self.client.decrypt(
            source=ciphertext_decoded, key_provider=self.key_provider, *args, **kwargs
        )

        if self.encryption_context != decrypted_header.encryption_context:
            raise ValueError("Encryption context mismatch")
        return ciphertext
