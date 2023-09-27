from __future__ import annotations

import base64
import json
from typing import Any, Callable, Dict, Union

import pytest

from aws_lambda_powertools.utilities.data_masking import DataMasking
from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING
from aws_lambda_powertools.utilities.data_masking.provider import BaseProvider
from aws_lambda_powertools.utilities.data_masking.provider.kms import (
    AwsEncryptionSdkProvider,
)


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


@pytest.fixture
def data_masker(monkeypatch) -> DataMasking:
    """DataMasking using AWS Encryption SDK Provider with a fake client"""
    fake_key_provider = FakeEncryptionKeyProvider()
    provider = AwsEncryptionSdkProvider(
        keys=["dummy"],
        key_provider=fake_key_provider,
    )
    return DataMasking(provider=provider)


def test_mask_int(data_masker):
    # GIVEN an int data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask(42)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_float(data_masker):
    # GIVEN a float data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask(4.2)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_bool(data_masker):
    # GIVEN a bool data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask(True)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_none(data_masker):
    # GIVEN a None data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask(None)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_str(data_masker):
    # GIVEN a str data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask("this is a string")

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_list(data_masker):
    # GIVEN a list data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask([1, 2, "string", 3])

    # THEN the result is the data masked, while maintaining type list
    assert masked_string == [DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING]


def test_mask_dict(data_masker):
    # GIVEN a dict data type
    data = {
        "a": {
            "1": {"None": "hello", "four": "world"},
            "b": {"3": {"4": "goodbye", "e": "world"}},
        },
    }

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask(data)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_dict_with_fields(data_masker):
    # GIVEN a dict data type
    data = {
        "a": {
            "1": {"None": "hello", "four": "world"},
            "b": {"3": {"4": "goodbye", "e": "world"}},
        },
    }

    # WHEN mask is called with a list of fields specified
    masked_string = data_masker.mask(data, fields=["a.1.None", "a.b.3.4"])

    # THEN the result is only the specified fields are masked
    assert masked_string == {
        "a": {
            "1": {"None": DATA_MASKING_STRING, "four": "world"},
            "b": {"3": {"4": DATA_MASKING_STRING, "e": "world"}},
        },
    }


def test_mask_json_dict_with_fields(data_masker):
    # GIVEN the data type is a json representation of a dictionary
    data = json.dumps(
        {
            "a": {
                "1": {"None": "hello", "four": "world"},
                "b": {"3": {"4": "goodbye", "e": "world"}},
            },
        },
    )

    # WHEN mask is called with a list of fields specified
    masked_json_string = data_masker.mask(data, fields=["a.1.None", "a.b.3.4"])

    # THEN the result is only the specified fields are masked
    assert masked_json_string == {
        "a": {
            "1": {"None": DATA_MASKING_STRING, "four": "world"},
            "b": {"3": {"4": DATA_MASKING_STRING, "e": "world"}},
        },
    }


def test_encrypt_int(data_masker):
    # GIVEN an int data type

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(-1)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == -1


def test_encrypt_float(data_masker):
    # GIVEN an float data type

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(-1.11)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == -1.11


def test_encrypt_bool(data_masker):
    # GIVEN an bool data type

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(True)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data is True


def test_encrypt_none(data_masker):
    # GIVEN an none data type

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(None)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data is None


def test_encrypt_str(data_masker):
    # GIVEN an str data type

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt("this is a string")
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == "this is a string"


def test_encrypt_list(data_masker):
    # GIVEN an list data type

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt([1, 2, "a string", 3.4])
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == [1, 2, "a string", 3.4]


def test_encrypt_dict(data_masker):
    # GIVEN an dict data type
    data = {
        "a": {
            "1": {"None": "hello", "four": "world"},
            "b": {"3": {"4": "goodbye", "e": "world"}},
        },
    }

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(data)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == data


def test_encrypt_dict_with_fields(data_masker):
    # GIVEN the data type is a dictionary
    data = {
        "a": {
            "1": {"None": "hello", "four": "world"},
            "b": {"3": {"4": "goodbye", "e": "world"}},
        },
    }

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(data, fields=["a.1.None", "a.b.3.4"])
    decrypted_data = data_masker.decrypt(encrypted_data, fields=["a.1.None", "a.b.3.4"])

    # THEN the result is only the specified fields are masked
    assert decrypted_data == data


def test_encrypt_json_dict_with_fields(data_masker):
    # GIVEN the data type is a json representation of a dictionary
    data = json.dumps(
        {
            "a": {
                "1": {"None": "hello", "four": "world"},
                "b": {"3": {"4": "goodbye", "e": "world"}},
            },
        },
    )

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(data, fields=["a.1.None", "a.b.3.4"])
    decrypted_data = data_masker.decrypt(encrypted_data, fields=["a.1.None", "a.b.3.4"])

    # THEN the result is only the specified fields are masked
    assert decrypted_data == json.loads(data)
