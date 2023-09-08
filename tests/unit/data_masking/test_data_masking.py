import json

import pytest

from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING


@pytest.fixture
def data_masker() -> DataMasking:
    return DataMasking()


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
    # GIVEN the data type is a dictionary
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


def test_encrypt_not_implemented(data_masker):
    # GIVEN DataMasking is not initialized with a Provider

    # WHEN attempting to call the encrypt method on the data

    # THEN the result is a NotImplementedError
    with pytest.raises(NotImplementedError):
        data_masker.encrypt("hello world")


def test_decrypt_not_implemented(data_masker):
    # GIVEN DataMasking is not initialized with a Provider

    # WHEN attempting to call the decrypt method on the data

    # THEN the result is a NotImplementedError
    with pytest.raises(NotImplementedError):
        data_masker.decrypt("hello world")


def test_parsing_unsupported_data_type(data_masker):
    # GIVEN an initialization of the DataMasking class

    # WHEN attempting to pass in a list of fields with input data that is not a dict

    # THEN the result is a TypeError
    with pytest.raises(TypeError):
        data_masker.mask(42, ["this.field"])


def test_parsing_nonexistent_fields(data_masker):
    # GIVEN an initialization of the DataMasking class

    data = {
        "3": {
            "1": {"None": "hello", "four": "world"},
            "4": {"33": {"5": "goodbye", "e": "world"}},
        },
    }

    # WHEN attempting to pass in fields that do not exist in the input data

    # THEN the result is a KeyError
    with pytest.raises(KeyError):
        data_masker.mask(data, ["3.1.True"])


def test_parsing_nonstring_fields(data_masker):
    # GIVEN an initialization of the DataMasking class

    data = {
        "3": {
            "1": {"None": "hello", "four": "world"},
            "4": {"33": {"5": "goodbye", "e": "world"}},
        },
    }

    # WHEN attempting to pass in a list of fields that are not strings
    masked = data_masker.mask(data, fields=[3.4])

    # THEN the result is the value of the nested field should be masked as normal
    assert masked == {"3": {"1": {"None": "hello", "four": "world"}, "4": DATA_MASKING_STRING}}


def test_parsing_nonstring_keys_and_fields(data_masker):
    # GIVEN an initialization of the DataMasking class

    # WHEN the input data is a dictionary with integer keys
    data = {
        3: {
            "1": {"None": "hello", "four": "world"},
            4: {"33": {"5": "goodbye", "e": "world"}},
        },
    }
    masked = data_masker.mask(data, fields=[3.4])

    # THEN the result is the value of the nested field should be masked as normal
    assert masked == {"3": {"1": {"None": "hello", "four": "world"}, "4": DATA_MASKING_STRING}}
