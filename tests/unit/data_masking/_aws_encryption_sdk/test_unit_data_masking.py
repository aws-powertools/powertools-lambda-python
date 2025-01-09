import json

import pytest

from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING
from aws_lambda_powertools.utilities.data_masking.exceptions import (
    DataMaskingFieldNotFoundError,
    DataMaskingUnsupportedTypeError,
)


@pytest.fixture
def data_masker() -> DataMasking:
    return DataMasking()


def test_erase_int(data_masker):
    # GIVEN an int data type

    # WHEN erase is called with no fields argument
    erased_string = data_masker.erase(42)

    # THEN the result is the data masked
    assert erased_string == DATA_MASKING_STRING


def test_erase_int_custom_mask(data_masker):
    # GIVEN an int data type

    # WHEN erase is called with no fields argument
    erased_string = data_masker.erase(42, custom_mask="XX")

    # THEN the result is the data masked
    assert erased_string == "XX"


def test_erase_float(data_masker):
    # GIVEN a float data type

    # WHEN erase is called with no fields argument
    erased_string = data_masker.erase(4.2)

    # THEN the result is the data masked
    assert erased_string == DATA_MASKING_STRING


def test_erase_bool(data_masker):
    # GIVEN a bool data type

    # WHEN erase is called with no fields argument
    erased_string = data_masker.erase(True)

    # THEN the result is the data masked
    assert erased_string == DATA_MASKING_STRING


def test_erase_none(data_masker):
    # GIVEN a None data type

    # WHEN erase is called with no fields argument
    erased_string = data_masker.erase(None)

    # THEN the result is the data masked
    assert erased_string == DATA_MASKING_STRING


def test_erase_str(data_masker):
    # GIVEN a str data type

    # WHEN erase is called with no fields argument
    erased_string = data_masker.erase("this is a string")

    # THEN the result is the data masked
    assert erased_string == DATA_MASKING_STRING


def test_erase_list(data_masker):
    # GIVEN a list data type

    # WHEN erase is called with no fields argument
    erased_string = data_masker.erase([1, 2, "string", 3])

    # THEN the result is the data masked, while maintaining type list
    assert erased_string == [DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING]


def test_erase_dict(data_masker):
    # GIVEN a dict data type
    data = {
        "a": {
            "1": {"None": "hello", "four": "world"},
            "b": {"3": {"4": "goodbye", "e": "world"}},
        },
    }

    # WHEN erase is called with no fields argument
    erased_string = data_masker.erase(data)

    # THEN the result is the data masked
    assert erased_string == DATA_MASKING_STRING


def test_erase_dict_with_fields(data_masker):
    # GIVEN a dict data type
    data = {
        "a": {
            "1": {"None": "hello", "four": "world"},
            "b": {"3": {"4": "goodbye", "e": "world"}},
        },
    }

    # WHEN erase is called with a list of fields specified
    erased_string = data_masker.erase(data, fields=["a.'1'.None", "a..'4'"])

    # THEN the result is only the specified fields are erased
    assert erased_string == {
        "a": {
            "1": {"None": DATA_MASKING_STRING, "four": "world"},
            "b": {"3": {"4": DATA_MASKING_STRING, "e": "world"}},
        },
    }


def test_erase_json_dict_with_fields(data_masker):
    # GIVEN the data type is a json representation of a dictionary
    data = json.dumps(
        {
            "a": {
                "1": {"None": "hello", "four": "world"},
                "b": {"3": {"4": "goodbye", "e": "world"}},
            },
        },
    )

    # WHEN erase is called with a list of fields specified
    masked_json_string = data_masker.erase(data, fields=["a.'1'.None", "a..'4'"])

    # THEN the result is only the specified fields are erased
    assert masked_json_string == {
        "a": {
            "1": {"None": DATA_MASKING_STRING, "four": "world"},
            "b": {"3": {"4": DATA_MASKING_STRING, "e": "world"}},
        },
    }


def test_encrypt_not_implemented(data_masker):
    # GIVEN DataMasking is not initialized with a Provider

    # WHEN attempting to call the encrypt method on the data
    with pytest.raises(NotImplementedError):
        # THEN the result is a NotImplementedError
        data_masker.encrypt("hello world")


def test_decrypt_not_implemented(data_masker):
    # GIVEN DataMasking is not initialized with a Provider

    # WHEN attempting to call the decrypt method on the data
    with pytest.raises(NotImplementedError):
        # THEN the result is a NotImplementedError
        data_masker.decrypt("hello world")


def test_parsing_unsupported_data_type(data_masker):
    # GIVEN an initialization of the DataMasking class

    # WHEN attempting to pass in a list of fields with input data that is not a dict
    with pytest.raises(DataMaskingUnsupportedTypeError):
        # THEN the result is a TypeError
        data_masker.erase(42, ["this.field"])


def test_parsing_with_empty_field(data_masker):
    # GIVEN an initialization of the DataMasking class

    # WHEN attempting to pass in a list of fields with input data that is not a dict
    with pytest.raises(ValueError):
        # THEN the result is a TypeError
        data_masker.erase(42, [])


def test_parsing_nonexistent_fields_with_raise_on_missing_field():
    # GIVEN a dict data type

    data_masker = DataMasking(raise_on_missing_field=True)
    data = {
        "3": {
            "1": {"None": "hello", "four": "world"},
            "4": {"33": {"5": "goodbye", "e": "world"}},
        },
    }

    # WHEN attempting to pass in fields that do not exist in the input data
    with pytest.raises(DataMaskingFieldNotFoundError):
        # THEN the result is a KeyError
        data_masker.erase(data, ["'3'..True"])


def test_parsing_nonexistent_fields_warning_on_missing_field():
    # GIVEN a dict data type

    data_masker = DataMasking(raise_on_missing_field=False)
    data = {
        "3": {
            "1": {"None": "hello", "four": "world"},
            "4": {"33": {"5": "goodbye", "e": "world"}},
        },
    }

    # WHEN erase is called with a non-existing field
    with pytest.warns(UserWarning, match="Field or expression*"):
        masked_json_string = data_masker.erase(data, fields=["non-existing"])

    # THEN the "erased" payload is the same of the original
    assert masked_json_string == data


def test_regex_mask(data_masker):
    data = "Hello! My name is Fulano Ciclano"
    regex_pattern = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
    mask_format = "XXXX XXXX"

    result = data_masker.erase(data, regex_pattern=regex_pattern, mask_format=mask_format)

    assert result == "Hello! My name is XXXX XXXX"


def test_erase_json_dict_with_fields_and_masks(data_masker):
    # GIVEN the data type is a json representation of a dictionary
    data = json.dumps(
        {
            "a": {
                "1": {"None": "hello", "four": "world"},
                "b": {"3": {"4": "goodbye", "e": "world"}},
            },
        },
    )

    # WHEN erase is called with a list of fields specified
    masked_json_string = data_masker.erase(data, fields=["a.'1'.None", "a..'4'"], dynamic_mask=True)

    # THEN the result is only the specified fields are erased
    assert masked_json_string == {
        "a": {
            "1": {"None": "*****", "four": "world"},
            "b": {"3": {"4": "*******", "e": "world"}},
        },
    }
