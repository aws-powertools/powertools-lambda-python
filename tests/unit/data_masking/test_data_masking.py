import json

import pytest
from aws_lambda_powertools.shared.constants import DATA_MASKING_STRING
from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from tests.unit.data_masking.setup import *

# should be conftest? no other conftest in unit tests
# didn't work when i made them all pytest.fixtures


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
