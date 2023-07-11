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
from aws_lambda_powertools.shared.user_agent import register_feature_to_botocore_session

class SingletonMeta(type):
    """Metaclass to cache class instances to optimize encryption"""

    _instances: Dict["AwsEncryptionSdkProvider", Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


CACHE_CAPACITY: int = 100
MAX_ENTRY_AGE_SECONDS: float = 300.0
MAX_MESSAGES: int = 200
# NOTE: You can also set max messages/bytes per data key


class AwsEncryptionSdkProvider(Provider, metaclass=SingletonMeta):
    cache = LocalCryptoMaterialsCache(CACHE_CAPACITY)
    session = botocore.session.Session()
register_feature_to_botocore_session(session, "data-masking")
    def __init__(self, keys: List[str], client: Optional[EncryptionSDKClient] = None) -> None:
        self.client = client or EncryptionSDKClient()
        self.keys = keys
        self.key_provider = StrictAwsKmsMasterKeyProvider(key_ids=self.keys, botocore_session=self.session)
        self.cache_cmm = CachingCryptoMaterialsManager(
            master_key_provider=self.key_provider,
            cache=self.cache,
            max_age=MAX_ENTRY_AGE_SECONDS,
            max_messages_encrypted=MAX_MESSAGES,
        )

    def encrypt(self, data: Union[bytes, str], *args, **kwargs) -> str:
        ciphertext, _ = self.client.encrypt(source=data, materials_manager=self.cache_cmm, *args, **kwargs)
        ciphertext = base64.b64encode(ciphertext).decode()
        return ciphertext

    def decrypt(self, data: str, *args, **kwargs) -> bytes:
        ciphertext_decoded = base64.b64decode(data)
        ciphertext, _ = self.client.decrypt(source=ciphertext_decoded, key_provider=self.key_provider, *args, **kwargs)
        return ciphertext
