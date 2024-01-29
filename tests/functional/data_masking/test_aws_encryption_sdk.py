from __future__ import annotations

import base64
import functools
import json
from typing import Any, Callable

import pytest
from aws_encryption_sdk.identifiers import Algorithm

from aws_lambda_powertools.utilities.data_masking import DataMasking
from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING
from aws_lambda_powertools.utilities.data_masking.provider import BaseProvider
from aws_lambda_powertools.utilities.data_masking.provider.kms import (
    AWSEncryptionSDKProvider,
)


class FakeEncryptionKeyProvider(BaseProvider):
    def __init__(
        self,
        json_serializer: Callable = functools.partial(json.dumps, ensure_ascii=False),
        json_deserializer: Callable = json.loads,
    ) -> None:
        super().__init__(json_serializer, json_deserializer)

    def encrypt(self, data: bytes | str, **kwargs) -> str:
        encoded_data: str = self.json_serializer(data)
        ciphertext = base64.b64encode(encoded_data.encode("utf-8")).decode()
        return ciphertext

    def decrypt(self, data: bytes, **kwargs) -> Any:
        ciphertext_decoded = base64.b64decode(data).decode("utf-8")
        ciphertext = self.json_deserializer(ciphertext_decoded)
        return ciphertext


@pytest.fixture
def data_masker(monkeypatch) -> DataMasking:
    """DataMasking using AWS Encryption SDK Provider with a fake client"""
    fake_key_provider = FakeEncryptionKeyProvider()
    provider = AWSEncryptionSDKProvider(
        keys=["dummy"],
        key_provider=fake_key_provider,
    )
    return DataMasking(provider=provider)


def test_mask_int(data_masker):
    # GIVEN an int data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.erase(42)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_float(data_masker):
    # GIVEN a float data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.erase(4.2)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_bool(data_masker):
    # GIVEN a bool data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.erase(True)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_none(data_masker):
    # GIVEN a None data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.erase(None)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_str(data_masker):
    # GIVEN a str data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.erase("this is a string")

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_list(data_masker):
    # GIVEN a list data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.erase([1, 2, "string", 3])

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
    masked_string = data_masker.erase(data)

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
    masked_string = data_masker.erase(data, fields=["a.'1'.None", "a..'4'"])

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
    masked_json_string = data_masker.erase(data, fields=["a.'1'.None", "a..'4'"])

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
    encrypted_data = data_masker.encrypt(data)
    decrypted_data = data_masker.decrypt(encrypted_data)

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
    encrypted_data = data_masker.encrypt(data)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is only the specified fields are masked
    assert decrypted_data == data


def test_encrypt_json_with_list_fields(data_masker):
    # GIVEN the data type is a json representation of a dictionary with a list inside
    data = json.dumps(
        {
            "payload": {
                "first": ["value1", "value2"],
                "second": [{"key1": [0, 1]}],
            },
        },
    )

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(data)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is only the specified fields are masked
    assert decrypted_data == data


def test_encrypt_json_with_tuple_fields(data_masker):
    # GIVEN the data type is a json representation of a dictionary with a list inside
    data = json.dumps(
        {
            "payload": {
                "first": ["value1", "value2"],
                "second": (0, 1),
            },
        },
    )

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(data)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is only the specified fields are masked
    assert decrypted_data == data


def test_encrypt_with_encryption_context(data_masker):
    # GIVEN the data type is a json representation of a dictionary with a list inside
    data = json.dumps(
        {
            "payload": {
                "first": ["value1", "value2"],
                "second": (0, 1),
            },
        },
    )

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(data, data_classification="confidential")
    decrypted_data = data_masker.decrypt(encrypted_data, data_classification="confidential")

    # THEN the result is only the specified fields are masked
    assert decrypted_data == data


def test_encrypt_with_complex_dict(data_masker):
    # GIVEN the data type is a json representation of a dictionary with a list inside
    data = json.dumps(
        {
            "name": "Leandro",
            "operation": "non sensitive",
            "card_number": "1000 4444 333 2222",
            "address": [
                {
                    "postcode": 81847,
                    "street": "38986 Joanne Stravenue",
                    "country": "United States",
                    "timezone": "America/La_Paz",
                },
                {
                    "postcode": 94400,
                    "street": "623 Kraig Mall",
                    "country": "United States",
                    "timezone": "America/Mazatlan",
                },
                {
                    "postcode": 94480,
                    "street": "123 Kraig Mall",
                    "country": "United States",
                    "timezone": "America/Mazatlan",
                },
            ],
        },
    )

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(data)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is only the specified fields are masked
    assert decrypted_data == data


def test_encrypt_with_slice(data_masker):
    # GIVEN the data type is a json representation of a dictionary with a list inside
    data = json.dumps(
        {
            "name": "Leandro",
            "operation": "non sensitive",
            "card_number": "1000 4444 333 2222",
            "address": [
                {
                    "postcode": 81847,
                    "street": "38986 Joanne Stravenue",
                    "country": "United States",
                    "timezone": "America/La_Paz",
                },
                {
                    "postcode": 94400,
                    "street": "623 Kraig Mall",
                    "country": "United States",
                    "timezone": "America/Mazatlan",
                },
                {
                    "postcode": 94480,
                    "street": "123 Kraig Mall",
                    "country": "United States",
                    "timezone": "America/Mazatlan",
                },
            ],
        },
    )

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(data)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is only the specified fields are masked
    assert decrypted_data == data


def test_encrypt_with_complex_search(data_masker):
    # GIVEN the data type is a json representation of a dictionary with a list inside
    data = json.dumps(
        {
            "name": "Leandro",
            "operation": "non sensitive",
            "card_number": "1000 4444 333 2222",
            "address": [
                {
                    "postcode": 81847,
                    "street": "38986 Joanne Stravenue",
                    "country": "United States",
                    "timezone": "America/La_Paz",
                },
                {
                    "postcode": 94400,
                    "street": "623 Kraig Mall",
                    "country": "United States",
                    "timezone": "America/Mazatlan",
                },
                {
                    "postcode": 94480,
                    "street": "123 Kraig Mall",
                    "country": "United States",
                    "timezone": "America/Mazatlan",
                },
            ],
        },
    )

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(data)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is only the specified fields are masked
    assert decrypted_data == data


def test_encrypt_with_provider_options(data_masker):
    # GIVEN the data type is a json representation of a dictionary with a list inside
    data = json.dumps(
        {
            "payload": {
                "first": ["value1", "value2"],
                "second": (0, 1),
            },
        },
    )

    provider_options = {"algorithm": Algorithm.AES_256_GCM_HKDF_SHA512_COMMIT_KEY}
    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(data, provider_options=provider_options)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is only the specified fields are masked
    assert decrypted_data == data
