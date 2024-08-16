from __future__ import annotations

import functools
import json
from typing import Any, Callable, Iterable

from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING


class BaseProvider:
    """
    The BaseProvider class serves as an abstract base class for data masking providers.

    Examples
    --------
    ```
    from aws_lambda_powertools.utilities._data_masking.provider import BaseProvider
    from aws_lambda_powertools.utilities.data_masking import DataMasking

    class MyCustomProvider(BaseProvider):
        def encrypt(self, data) -> str:
            # Implementation logic for data encryption

        def decrypt(self, data) -> Any:
            # Implementation logic for data decryption

        def erase(self, data) -> str | Iterable:
            # Implementation logic for data masking
            pass

    def lambda_handler(event, context):
        provider = MyCustomProvider(["secret-key"])
        data_masker = DataMasking(provider=provider)

        data = {
            "project": "powertools",
            "sensitive": "password"
        }

        encrypted = data_masker.encrypt(data)

        return encrypted
    ```
    """

    def __init__(
        self,
        json_serializer: Callable[..., str] = functools.partial(json.dumps, ensure_ascii=False),
        json_deserializer: Callable[[str], Any] = json.loads,
    ) -> None:
        self.json_serializer = json_serializer
        self.json_deserializer = json_deserializer

    def encrypt(self, data, provider_options: dict | None = None, **encryption_context: str) -> str:
        """
        Abstract method for encrypting data. Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement encrypt()")

    def decrypt(self, data, provider_options: dict | None = None, **encryption_context: str) -> Any:
        """
        Abstract method for decrypting data. Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement decrypt()")

    def erase(self, data, **kwargs) -> Iterable[str]:
        """
        This method irreversibly erases data.

        If the data to be erased is of type `str`, `dict`, or `bytes`,
        this method will return an erased string, i.e. "*****".

        If the data to be erased is of an iterable type like `list`, `tuple`,
        or `set`, this method will return a new object of the same type as the
        input data but with each element replaced by the string "*****".
        """
        if isinstance(data, (str, dict, bytes)):
            return DATA_MASKING_STRING
        elif isinstance(data, (list, tuple, set)):
            return type(data)([DATA_MASKING_STRING] * len(data))
        return DATA_MASKING_STRING
