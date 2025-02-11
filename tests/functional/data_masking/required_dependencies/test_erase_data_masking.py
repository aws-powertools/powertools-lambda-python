import json

import pytest

from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING
from aws_lambda_powertools.utilities.data_masking.exceptions import (
    DataMaskingFieldNotFoundError,
    DataMaskingUnsupportedTypeError,
)
from aws_lambda_powertools.warnings import PowertoolsUserWarning


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
    # GIVEN a str data type
    data = "Hello! My name is John Doe"

    # WHEN erase is called with regex pattern and mask format
    regex_pattern = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
    mask_format = "XXXX XXXX"

    result = data_masker.erase(data, regex_pattern=regex_pattern, mask_format=mask_format)

    # THEN the result is the regex part masked by the masked format
    assert result == "Hello! My name is XXXX XXXX"


def test_regex_mask_with_cache(data_masker):
    # GIVEN a str data type
    data = "Hello! My name is John Doe"
    data1 = "Hello! My name is John Xix"

    # WHEN erase is called with regex pattern and mask format
    regex_pattern = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
    mask_format = "XXXX XXXX"

    # WHEN erasing twice to check the regex compiled and stored in the cache
    result = data_masker.erase(data, regex_pattern=regex_pattern, mask_format=mask_format)
    result1 = data_masker.erase(data1, regex_pattern=regex_pattern, mask_format=mask_format)

    # THEN the result is the regex part masked by the masked format
    assert result == "Hello! My name is XXXX XXXX"
    assert result1 == "Hello! My name is XXXX XXXX"


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


def test_erase_json_dict_with_complex_masking_rules(data_masker):
    # GIVEN the data type is a json representation of a dictionary with nested and filtered paths
    data = {
        "email": "johndoe@example.com",
        "age": 30,
        "address": {"zip": 13000, "street": "123 Main St", "details": {"name": "Home", "type": "Primary"}},
    }

    # WHEN erase is called with complex masking rules
    masking_rules = {
        "email": {"regex_pattern": "(.)(.*)(@.*)", "mask_format": r"\1****\3"},
        "age": {"dynamic_mask": True},
        "address.zip": {"custom_mask": "xxx"},
    }

    masked_json_string = data_masker.erase(data=data, masking_rules=masking_rules)

    # THEN the result should have all specified fields masked according to their rules
    assert masked_json_string == {
        "email": "j****@example.com",
        "age": "**",
        "address": {"zip": "xxx", "street": "123 Main St", "details": {"name": "Home", "type": "Primary"}},
    }


def test_dynamic_mask_with_string(data_masker):
    # GIVEN the data type is a json representation of a dictionary with nested and filtered paths
    data = "XYZEKDEDE"

    masked_json_string = data_masker.erase(data=data, dynamic_mask=True)

    # THEN the result should have all specified fields masked according to their rules
    assert masked_json_string == "*********"


def test_no_matches_for_masking_rule(data_masker):
    # GIVEN a dictionary without the expected field
    data = {"name": "Ana"}
    masking_rules = {"$.missing_field": {"dynamic_mask": True}}

    # WHEN applying the masking rule
    with pytest.warns(UserWarning, match=r"No matches found *"):
        result = data_masker.erase(data=data, masking_rules=masking_rules)

    # THEN the original data remains unchanged
    assert result == data


def test_warning_during_masking_value(data_masker):
    # GIVEN data and a masking rule
    data = {"value": "test"}

    # Mock provider that raises an error
    class MockProvider:
        def erase(self, value, **kwargs):
            raise ValueError("Mock error")

    data_masker.provider = MockProvider()

    # WHEN erase is called
    with pytest.warns(expected_warning=PowertoolsUserWarning, match="Error masking value for path value: Mock error"):
        masked_data = data_masker.erase(data, masking_rules={"value": {"rule": "value"}})

    # THEN the original data should remain unchanged
    assert masked_data["value"] == "test"


def test_mask_nested_field_success(data_masker):
    # GIVEN nested data with a field to mask
    data = {"user": {"contact": {"details": {"address": {"street": "123 Main St", "zip": "12345"}}}}}

    # WHEN masking a nested field with a masking rule
    data_masked = data_masker.erase(data=data, fields=["user.contact.details.address.zip"], custom_mask="xxx")

    # THEN the nested field should be masked while other data remains unchanged
    assert data_masked == {"user": {"contact": {"details": {"address": {"street": "123 Main St", "zip": "xxx"}}}}}


def test_erase_dictionary_with_masking_rules(data_masker):
    # GIVEN a dictionary with nested sensitive data
    data = {"user": {"name": "John Doe", "ssn": "123-45-6789", "address": {"street": "123 Main St", "zip": "12345"}}}

    # AND masking rules for specific fields
    masking_rules = {"user.ssn": {"custom_mask": "XXX-XX-XXXX"}, "user.address.zip": {"custom_mask": "00000"}}

    # WHEN erase is called with masking rules
    result = data_masker.erase(data, masking_rules=masking_rules)

    # THEN only the specified fields should be masked
    assert result == {
        "user": {
            "name": "John Doe",  # unchanged
            "ssn": "XXX-XX-XXXX",  # masked
            "address": {"street": "123 Main St", "zip": "00000"},  # unchanged  # masked
        },
    }


def test_erase_dictionary_with_masking_rules_with_list(data_masker):
    # GIVEN a dictionary with nested sensitive data
    data = {"user": {"name": ["leandro", "powertools"]}}

    # AND masking rules for specific fields
    masking_rules = {"user.name": {"custom_mask": "NO-NAME"}}

    # WHEN erase is called with masking rules
    result = data_masker.erase(data, masking_rules=masking_rules)

    # THEN only the specified fields should be masked
    assert result == {
        "user": {
            "name": "NO-NAME",
        },
    }


def test_erase_list_with_custom_mask(data_masker):
    # GIVEN a dictionary with nested sensitive data
    data = {"user": {"name": ["leandro", "powertools"]}}

    # WHEN erase is called with masking rules
    result = data_masker.erase(data, fields=["user.name"], dynamic_mask=True)

    # THEN only the specified fields should be masked
    assert result == {
        "user": {
            "name": ["*******", "**********"],
        },
    }


def test_erase_dictionary_with_global_mask(data_masker):
    # GIVEN a dictionary with sensitive data
    data = {"user": {"name": "John Doe", "ssn": "123-45-6789"}}

    # WHEN erase is called with a custom mask for all fields
    result = data_masker.erase(data, custom_mask="REDACTED")

    # THEN all fields should use the custom mask
    assert result == {"user": {"name": "REDACTED", "ssn": "REDACTED"}}


def test_erase_empty_dictionary(data_masker):
    # GIVEN an empty dictionary
    data = {}

    # WHEN erase is called
    result = data_masker.erase(data, custom_mask="MASKED")

    # THEN an empty dictionary should be returned
    assert result == {}


def test_erase_different_iterables_with_masking(data_masker):
    # GIVEN different types of iterables
    list_data = ["name", "phone", "email"]
    tuple_data = ("name", "phone", "email")
    set_data = {"name", "phone", "email"}

    # WHEN erase is called with a custom mask
    masked_list = data_masker.erase(list_data, custom_mask="XXX")
    masked_tuple = data_masker.erase(tuple_data, custom_mask="XXX")
    masked_set = data_masker.erase(set_data, custom_mask="XXX")

    # THEN the masked data should maintain its original type
    assert isinstance(masked_list, list)
    assert isinstance(masked_tuple, tuple)
    assert isinstance(masked_set, set)

    # AND all values should be masked
    expected_values = {"XXX"}
    assert set(masked_list) == expected_values
    assert set(masked_tuple) == expected_values
    assert masked_set == expected_values


def test_erase_handles_invalid_regex_pattern(data_masker):
    # GIVEN a string and an invalid regex pattern
    data = "test123"

    # WHEN masking with invalid regex
    result = data_masker.erase(
        data,
        regex_pattern="[",
        mask_format="X",  # Invalid regex pattern that will raise re.error
    )

    # THEN original data should be returned
    assert result == "test123"


def test_erase_handles_empty_string_with_dynamic_mask(data_masker):
    # GIVEN an empty string
    data = ""

    # WHEN erase is called with dynamic_mask
    result = data_masker.erase(data, dynamic_mask=True)

    # THEN empty string should be returned
    assert result == ""


def test_erase_dictionary_with_masking_rules_wrong_field(data_masker):
    # GIVEN a dictionary with nested sensitive data
    data = {"user": {"name": "John Doe", "ssn": "123-45-6789", "address": {"street": "123 Main St", "zip": "12345"}}}

    # AND masking rules for specific fields
    masking_rules = {"user.ssn...": {"custom_mask": "XXX-XX-XXXX"}, "user.address.zip": {"custom_mask": "00000"}}

    # WHEN erase is called with wrong masking rules
    # We must have a warning
    with pytest.warns(expected_warning=PowertoolsUserWarning, match="Error processing path*"):
        data_masker.erase(data, masking_rules=masking_rules)
