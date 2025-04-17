from __future__ import annotations

import functools
import json
import re
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING

if TYPE_CHECKING:
    from collections.abc import Callable

PRESERVE_CHARS = set("-_. ")
_regex_cache = {}

JSON_DUMPS_CALL = functools.partial(json.dumps, ensure_ascii=False)


class BaseProvider:
    """
    The BaseProvider class serves as an abstract base class for data masking providers.

    Example
    --------
    ```python
    from aws_lambda_powertools.utilities._data_masking.provider import BaseProvider
    from aws_lambda_powertools.utilities.data_masking import DataMasking

    class MyCustomProvider(BaseProvider):
        def encrypt(self, data) -> str:
            # Implementation logic for data encryption

        def decrypt(self, data) -> Any:
            # Implementation logic for data decryption

        def erase(self, data) -> Any | Iterable:
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
        json_serializer: Callable[..., str] = JSON_DUMPS_CALL,
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

    def erase(
        self,
        data: Any,
        dynamic_mask: bool | None = None,
        custom_mask: str | None = None,
        regex_pattern: str | None = None,
        mask_format: str | None = None,
        masking_rules: dict | None = None,
        **kwargs,
    ) -> Any:
        result: Any = DATA_MASKING_STRING

        if not any([dynamic_mask, custom_mask, regex_pattern, mask_format, masking_rules]):
            if isinstance(data, (str, int, float, dict, bytes)):
                return DATA_MASKING_STRING
            elif isinstance(data, (list, tuple, set)):
                return type(data)([DATA_MASKING_STRING] * len(data))
            else:
                return DATA_MASKING_STRING

        if isinstance(data, (str, int, float)):
            result = self._mask_primitive(str(data), dynamic_mask, custom_mask, regex_pattern, mask_format)
        elif isinstance(data, dict):
            result = self._mask_dict(
                data,
                dynamic_mask,
                custom_mask,
                regex_pattern,
                mask_format,
                masking_rules,
            )
        elif isinstance(data, (list, tuple, set)):
            result = self._mask_iterable(
                data,
                dynamic_mask,
                custom_mask,
                regex_pattern,
                mask_format,
                masking_rules,
            )

        return result

    def _mask_primitive(
        self,
        data: str,
        dynamic_mask: bool | None,
        custom_mask: str | None,
        regex_pattern: str | None,
        mask_format: str | None,
    ) -> str:
        if regex_pattern and mask_format:
            return self._regex_mask(data, regex_pattern, mask_format)
        elif custom_mask:
            return self._pattern_mask(data, custom_mask)

        return self._custom_erase(data)

    def _mask_dict(
        self,
        data: dict,
        dynamic_mask: bool | None,
        custom_mask: str | None,
        regex_pattern: str | None,
        mask_format: str | None,
        masking_rules: dict | None,
    ) -> dict:
        return {
            k: self.erase(
                v,
                dynamic_mask=dynamic_mask,
                custom_mask=custom_mask,
                regex_pattern=regex_pattern,
                mask_format=mask_format,
                masking_rules=masking_rules,
            )
            for k, v in data.items()
        }

    def _mask_iterable(
        self,
        data: list | tuple | set,
        dynamic_mask: bool | None,
        custom_mask: str | None,
        regex_pattern: str | None,
        mask_format: str | None,
        masking_rules: dict | None,
    ) -> list | tuple | set:
        masked_data = [
            self.erase(
                item,
                dynamic_mask=dynamic_mask,
                custom_mask=custom_mask,
                regex_pattern=regex_pattern,
                mask_format=mask_format,
                masking_rules=masking_rules,
            )
            for item in data
        ]
        return type(data)(masked_data)

    def _pattern_mask(self, data: str, pattern: str) -> str:
        """Apply pattern masking to string data."""
        return pattern[: len(data)] if len(pattern) >= len(data) else pattern

    def _regex_mask(self, data: str, regex_pattern: str, mask_format: str) -> str:
        """Apply regex masking to string data."""
        try:
            if regex_pattern not in _regex_cache:
                _regex_cache[regex_pattern] = re.compile(regex_pattern)
            return _regex_cache[regex_pattern].sub(mask_format, data)
        except re.error:
            return data

    def _custom_erase(self, data: str) -> str:
        if not data:
            return ""

        return "".join("*" if char not in PRESERVE_CHARS else char for char in data)
