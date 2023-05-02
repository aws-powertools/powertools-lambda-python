import botocore
from aws_lambda_powertools.shared import DATA_MASKING_STRING as MASK
from typing import Any, Optional, Union
import base64
import json
from abc import abstractmethod
from collections.abc import Iterable
from itsdangerous.url_safe import URLSafeSerializer
from aws_encryption_sdk import (
    CachingCryptoMaterialsManager,
    EncryptionSDKClient,
    LocalCryptoMaterialsCache,
    StrictAwsKmsMasterKeyProvider,
)

class Provider():

    '''
    When you try to create an instance of a subclass that does not implement the encrypt method, 
    you will get a NotImplementedError with a message that says the method is not implemented:
    '''
    @abstractmethod
    def encrypt(self, data):
        raise NotImplementedError("Subclasses must implement encrypt()")

    @abstractmethod
    def decrypt(self, data):
        raise NotImplementedError("Subclasses must implement decrypt()")

    def mask(self, data):
        if isinstance(data, (str, dict, bytes)):
            return MASK
        elif isinstance(data, Iterable):
            return type(data)([MASK] * len(data))
        return MASK
        


class DataMasking():
    def __init__(self, provider=None):
        if provider is None:
            self.provider = Provider()
        else:
            self.provider = provider

    def encrypt(self, data, fields=None, *args, context: Optional[dict] = {}, **kwargs):
        return self._apply_action(data, fields, action=self.provider.encrypt, *args, *context, **kwargs)

    def decrypt(self, data, fields=None, *args, context: Optional[dict] = {}, **kwargs):
        return self._apply_action(data, fields, action=self.provider.decrypt, *args, *context, **kwargs)

    def mask(self, data, fields=None, *args, **kwargs):
        return self._apply_action(data, fields, action=self.provider.mask, *args, **kwargs)

    def _apply_action(self, data, fields, action, *args, **kwargs):
        if fields is not None:
            return self._use_ast(data, fields, action=action, *args, **kwargs)
        else:
            return action(data, *args, **kwargs)

    def _default_mask(self, data, fields=None, *args, **kwargs):
        if isinstance(data, (str, dict, bytes)):
            return MASK
        elif isinstance(data, Iterable):
            return type(data)([MASK] * len(data))
        return MASK

    def _use_ast(self, data: Union[dict, str], fields, action, *args, **kwargs) -> str:
        if fields is None:
            raise ValueError("No fields specified.")
        if (isinstance(data, str)):
            # Parse JSON string as dictionary
            my_dict_parsed = json.loads(data)
            
        elif (isinstance(data, dict)):            
            # Turn into json string so everything has quotes around it
            my_dict_parsed = json.dumps(data)
            # Turn back into dict so can parse it
            my_dict_parsed = json.loads(my_dict_parsed)
        else:
            raise TypeError("Unsupported data type. The 'data' parameter must be a dictionary or a JSON string representation of a dictionary.")

        for field in fields:
            if (not isinstance(field, str)):
                field = json.dumps(field)
            keys = field.split('.')

            curr_dict = my_dict_parsed
            for key in keys[:-1]:
                curr_dict = curr_dict[key]
            valtochange = curr_dict[(keys[-1])]
            curr_dict[keys[-1]] = action(valtochange)
        
        return my_dict_parsed


class ItsDangerousProvider(Provider):
    def __init__(self, keys, salt=None):
        self.keys = keys
        self.salt = salt
    
    def encrypt(self, value, **kwargs) -> str:
        if value is None:
            return value
        
        s = URLSafeSerializer(self.keys, salt=self.salt)
        return s.dumps(value)

    def decrypt(self, value, **kwargs) -> str:
        if value is None:
            return value

        s = URLSafeSerializer(self.keys, salt=self.salt)
        return s.loads(value)

    def mask(self, value):
        return super().mask(value)


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

    def __init__(self, keys: list[str], client: Optional[EncryptionSDKClient] = None) -> None:
        self.client = client or EncryptionSDKClient()
        self.keys = keys
        self.key_provider = StrictAwsKmsMasterKeyProvider(key_ids=self.keys, botocore_session=self.session)
        self.cache_cmm = CachingCryptoMaterialsManager(
            master_key_provider=self.key_provider,
            cache=self.cache,
            max_age=self.MAX_ENTRY_AGE_SECONDS,
            max_messages_encrypted=self.MAX_MESSAGES,
        )

    def encrypt(self, plaintext: Union[bytes, str], context: Optional[dict] = {}, **kwargs) -> str:
        ciphertext, header = self.client.encrypt(source=plaintext, encryption_context=context, materials_manager=self.cache_cmm)
        ciphertext = base64.b64encode(ciphertext).decode()
        self.encryption_context = header.encryption_context
        return ciphertext

    def decrypt(self, encoded_ciphertext: str, context: Optional[dict] = {}, **kwargs) -> bytes:
        ciphertext_decoded = base64.b64decode(encoded_ciphertext)
        ciphertext, decrypted_header = self.client.decrypt(source=ciphertext_decoded, key_provider=self.key_provider)

        if (self.encryption_context != decrypted_header.encryption_context):
            raise ValueError("Encryption context mismatch")
        return ciphertext

    def mask(self, value):
        return super().mask(value)