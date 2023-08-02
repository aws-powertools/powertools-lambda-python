import copy
import json

import pytest
from itsdangerous.url_safe import URLSafeSerializer

from aws_lambda_powertools.shared.constants import DATA_MASKING_STRING
from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from aws_lambda_powertools.utilities.data_masking.provider import Provider


class MyEncryptionProvider(Provider):
    """Custom encryption provider class"""

    def __init__(self, keys, salt=None):
        self.keys = keys
        self.salt = salt

    def encrypt(self, data: str) -> str:
        if data is None:
            return data
        serialize = URLSafeSerializer(self.keys)
        return serialize.dumps(data)

    def decrypt(self, data: str) -> str:
        if data is None:
            return data
        serialize = URLSafeSerializer(self.keys)
        return serialize.loads(data)


data_maskers = [
    DataMasking(),
    DataMasking(provider=MyEncryptionProvider(keys="secret-key")),
]


python_dict = {
    "a": {
        "1": {"None": "hello", "four": "world"},  # None type key doesn't work
        "b": {"3": {"4": "goodbye", "e": "world"}},  # key "4.5" doesn't work
    }
}
json_dict = json.dumps(python_dict)
dict_fields = ["a.1.None", "a.b.3.4"]
masked_with_fields = {
    "a": {"1": {"None": DATA_MASKING_STRING, "four": "world"}, "b": {"3": {"4": DATA_MASKING_STRING, "e": "world"}}}
}
aws_encrypted_with_fields = {
    "a": {
        "1": {"None": bytes("hello", "utf-8"), "four": "world"},
        "b": {"3": {"4": bytes("goodbye", "utf-8"), "e": "world"}},
    }
}

# 10kb JSON blob for latency testing
json_blob = {
    "id": 1,
    "name": "John Doe",
    "age": 30,
    "email": "johndoe@example.com",
    "address": {"street": "123 Main St", "city": "Anytown", "state": "CA", "zip": "12345"},
    "phone_numbers": ["+1-555-555-1234", "+1-555-555-5678"],
    "interests": ["Hiking", "Traveling", "Photography", "Reading"],
    "job_history": {
        "company": "Acme Inc.",
        "position": "Software Engineer",
        "start_date": "2015-01-01",
        "end_date": "2017-12-31",
    },
    "about_me": """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla tincidunt velit quis
    sapien mollis, at egestas massa tincidunt. Suspendisse ultrices arcu a dolor dapibus,
    ut pretium turpis volutpat. Vestibulum at sapien quis sapien dignissim volutpat ut a enim.
    Praesent fringilla sem eu dui convallis luctus. Donec ullamcorper, sapien ut convallis congue,
    risus mauris pretium tortor, nec dignissim arcu urna a nisl. Vivamus non fermentum ex. Proin
    interdum nisi id sagittis egestas. Nam sit amet nisi nec quam pharetra sagittis. Aliquam erat
    volutpat. Donec nec luctus sem, nec ornare lorem. Vivamus vitae orci quis enim faucibus placerat.
    Nulla facilisi. Proin in turpis orci. Donec imperdiet velit ac tellus gravida, eget laoreet tellus
    malesuada. Praesent venenatis tellus ac urna blandit, at varius felis posuere. Integer a commodo nunc.
    """,
}
json_blob_fields = ["address.street", "job_history.company"]
aws_encrypted_json_blob = copy.deepcopy(json_blob)
aws_encrypted_json_blob["address"]["street"] = bytes("123 Main St", "utf-8")
aws_encrypted_json_blob["job_history"]["company"] = bytes("Acme Inc.", "utf-8")

dictionaries = [python_dict, json_dict, json_blob]
fields_to_mask = [dict_fields, dict_fields, json_blob_fields]

data_types_and_masks = [
    # simple data types
    [42, DATA_MASKING_STRING],
    [4.22, DATA_MASKING_STRING],
    [True, DATA_MASKING_STRING],
    [None, DATA_MASKING_STRING],
    ["this is a string", DATA_MASKING_STRING],
    # iterables
    [[1, 2, 3, 4], [DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING]],
    [
        ["hello", 1, 2, 3, "world"],
        [DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING],
    ],
    # dictionaries
    [python_dict, DATA_MASKING_STRING],
    [json_dict, DATA_MASKING_STRING],
]
data_types = [item[0] for item in data_types_and_masks]


@pytest.mark.parametrize("data_masker", data_maskers)
@pytest.mark.parametrize("value, value_masked", data_types_and_masks)
def test_mask_types(data_masker, value, value_masked):
    # GIVEN any data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask(value)

    # THEN the result is the full input data masked
    assert masked_string == value_masked


@pytest.mark.parametrize("data_masker", data_maskers)
def test_mask_with_fields(data_masker):
    # GIVEN the data type is a dictionary, or a json representation of a dictionary

    # WHEN mask is called with a list of fields specified
    masked_string = data_masker.mask(python_dict, dict_fields)
    masked_json_string = data_masker.mask(json_dict, dict_fields)

    # THEN the result is only the specified fields are masked
    assert masked_string == masked_with_fields
    assert masked_json_string == masked_with_fields


@pytest.mark.parametrize("value", data_types)
def test_encrypt_decrypt(value):
    # GIVEN an instantiation of DataMasking with a Provider
    data_masker = DataMasking(provider=MyEncryptionProvider(keys="secret-key"))

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(value)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == value


@pytest.mark.parametrize("value, fields", zip(dictionaries, fields_to_mask))
def test_encrypt_decrypt_with_fields(value, fields):
    # GIVEN an instantiation of DataMasking with a Provider
    data_masker = DataMasking(provider=MyEncryptionProvider(keys="secret-key"))

    # WHEN encrypting and then decrypting the encrypted data with a list of fields
    encrypted_data = data_masker.encrypt(value, fields)
    decrypted_data = data_masker.decrypt(encrypted_data, fields)

    # THEN the result is the original input data
    if value == json_dict:
        assert decrypted_data == json.loads(value)
    else:
        assert decrypted_data == value


def test_encrypt_not_implemented():
    # GIVEN DataMasking is not initialized with a Provider
    data_masker = DataMasking()

    # WHEN attempting to call the encrypt method on the data

    # THEN the result is a NotImplementedError
    with pytest.raises(NotImplementedError):
        data_masker.encrypt("hello world")


def test_decrypt_not_implemented():
    # GIVEN DataMasking is not initialized with a Provider
    data_masker = DataMasking()

    # WHEN attempting to call the decrypt method on the data

    # THEN the result is a NotImplementedError
    with pytest.raises(NotImplementedError):
        data_masker.decrypt("hello world")


def test_parsing_unsupported_data_type():
    # GIVEN an initialization of the DataMasking class
    data_masker = DataMasking()

    # WHEN attempting to pass in a list of fields with input data that is not a dict

    # THEN the result is a TypeError
    with pytest.raises(TypeError):
        data_masker.mask(42, ["this.field"])


def test_parsing_nonexistent_fields():
    # GIVEN an initialization of the DataMasking class
    data_masker = DataMasking()
    _python_dict = {
        "3": {
            "1": {"None": "hello", "four": "world"},
            "4": {"33": {"5": "goodbye", "e": "world"}},
        }
    }

    # WHEN attempting to pass in fields that do not exist in the input data

    # THEN the result is a KeyError
    with pytest.raises(KeyError):
        data_masker.mask(_python_dict, ["3.1.True"])


def test_parsing_nonstring_fields():
    # GIVEN an initialization of the DataMasking class
    data_masker = DataMasking()
    _python_dict = {
        "3": {
            "1": {"None": "hello", "four": "world"},
            "4": {"33": {"5": "goodbye", "e": "world"}},
        }
    }

    # WHEN attempting to pass in a list of fields that are not strings
    masked = data_masker.mask(_python_dict, fields=[3.4])

    # THEN the result is the value of the nested field should be masked as normal
    assert masked == {"3": {"1": {"None": "hello", "four": "world"}, "4": DATA_MASKING_STRING}}


def test_parsing_nonstring_keys_and_fields():
    # GIVEN an initialization of the DataMasking class
    data_masker = DataMasking()

    # WHEN the input data is a dictionary with integer keys
    _python_dict = {
        3: {
            "1": {"None": "hello", "four": "world"},
            4: {"33": {"5": "goodbye", "e": "world"}},
        }
    }

    masked = data_masker.mask(_python_dict, fields=[3.4])

    # THEN the result is the value of the nested field should be masked as normal
    assert masked == {"3": {"1": {"None": "hello", "four": "world"}, "4": DATA_MASKING_STRING}}
