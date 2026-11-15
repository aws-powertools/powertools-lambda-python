from __future__ import annotations

import enum
import json

import pytest

from aws_lambda_powertools.utilities.data_masking.base import DataMasking, prepare_data
from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING
from aws_lambda_powertools.utilities.data_masking.exceptions import (
    DataMaskingError,
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
    with pytest.raises(DataMaskingFieldNotFoundError, match=r"Field or expression .* not found"):
        data_masker.erase(data=data, masking_rules=masking_rules)


def test_no_matches_for_masking_rule_warning():
    # GIVEN a dictionary without the expected field
    data_masker = DataMasking(raise_on_missing_field=False)
    data = {"name": "Ana"}
    masking_rules = {"$.missing_field": {"dynamic_mask": True}}

    # WHEN applying the masking rule
    with pytest.warns(UserWarning, match=r"No matches found *"):
        result = data_masker.erase(data=data, masking_rules=masking_rules)

    # THEN the original data remains unchanged
    assert result == data


def test_error_during_masking_value(data_masker):
    # GIVEN data and a masking rule
    data = {"value": "test"}

    # Mock provider that raises an error
    class MockProvider:
        def erase(self, value, **kwargs):
            raise ValueError("Mock error")

    data_masker.provider = MockProvider()

    # WHEN erase is called
    with pytest.raises(DataMaskingError, match="Failed to mask field at path: value") as exc_info:
        data_masker.erase(data, masking_rules={"value": {"rule": "value"}})

    # THEN the provider error is preserved
    assert isinstance(exc_info.value.__cause__, ValueError)


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
    data = {"user": {"name": ["Pat", "powertools"]}}

    # AND masking rules for specific fields
    masking_rules = {"user.name": {"custom_mask": "NO-NAME"}}

    # WHEN erase is called with masking rules
    result = data_masker.erase(data, masking_rules=masking_rules)

    # THEN the rule is applied to each element, like the fields path does,
    # instead of to the Python repr of the list (which also changed the type to str)
    assert result == {
        "user": {
            "name": ["NO-", "NO-NAME"],
        },
    }


def test_erase_list_with_custom_mask(data_masker):
    # GIVEN a dictionary with nested sensitive data
    data = {"user": {"name": ["Pat", "powertools"]}}

    # WHEN erase is called with masking rules
    result = data_masker.erase(data, fields=["user.name"], dynamic_mask=True)

    # THEN only the specified fields should be masked
    assert result == {
        "user": {
            "name": ["***", "**********"],
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
    with pytest.raises(DataMaskingError, match="Invalid regex pattern"):
        data_masker.erase(
            data,
            regex_pattern="[",
            mask_format="X",  # Invalid regex pattern that will raise re.error
        )


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
    with pytest.raises(DataMaskingError, match="Invalid masking path"):
        data_masker.erase(data, masking_rules=masking_rules)


def test_erase_fields_and_masking_rules_together_raise(data_masker):
    # GIVEN both fields and masking_rules
    data = {"a": "value-a", "b": "value-b"}

    # WHEN erase is called with both
    # THEN it raises instead of silently ignoring fields
    with pytest.raises(DataMaskingError, match="cannot be used together"):
        data_masker.erase(data, fields=["a"], masking_rules={"b": {"dynamic_mask": True}})


def test_erase_json_string_with_masking_rules(data_masker):
    # GIVEN a JSON string and masking rules
    data = json.dumps({"user": {"name": "Pat", "team": "powertools"}})

    # WHEN erase is called with masking rules
    result = data_masker.erase(data, masking_rules={"user.name": {"custom_mask": "XXX"}})

    # THEN the string is parsed like the fields path does and the rule is applied
    assert result == {"user": {"name": "XXX", "team": "powertools"}}


def test_erase_json_string_with_masking_rules_lenient_mode_still_masks():
    # GIVEN a lenient masker and a JSON string
    data_masker = DataMasking(raise_on_missing_field=False)
    data = json.dumps({"user": {"name": "Pat"}})

    # WHEN erase is called with masking rules
    result = data_masker.erase(data, masking_rules={"user.name": {"dynamic_mask": True}})

    # THEN the field is masked instead of the original string coming back untouched
    assert result == {"user": {"name": "***"}}


def test_erase_masking_rules_recurse_into_nested_dict(data_masker):
    # GIVEN a rule pointing at a dict value
    data = {"user": {"contact": {"email": "pat@example.com", "phone": "555-0100"}}}

    # WHEN erase is called with a rule on the parent key
    result = data_masker.erase(data, masking_rules={"user.contact": {"dynamic_mask": True}})

    # THEN every value under it is masked and the structure is preserved
    assert result == {"user": {"contact": {"email": "***********.***", "phone": "***-****"}}}


def test_prepare_data_same_object_referenced_twice():
    # GIVEN a plain object referenced twice in the same structure
    class Customer:
        def __init__(self, name):
            self.name = name

    customer = Customer("Pat")
    data = {"payer": customer, "beneficiary": customer}

    # WHEN preparing the data
    result = prepare_data(data)

    # THEN both references are converted; a shared reference is not a cycle
    assert result == {"payer": {"name": "Pat"}, "beneficiary": {"name": "Pat"}}


def test_prepare_data_object_with_slots():
    # GIVEN an object that uses __slots__ and therefore has no __dict__
    class Card:
        __slots__ = ("number", "holder")

        def __init__(self):
            self.number = "4111"
            self.holder = "Pat"

    # WHEN preparing a list of them
    result = prepare_data([Card(), Card()])

    # THEN they are converted to dicts like any other object
    assert result == [{"number": "4111", "holder": "Pat"}, {"number": "4111", "holder": "Pat"}]


def test_prepare_data_circular_reference_still_handled():
    # GIVEN an object that references itself
    class Node:
        def __init__(self):
            self.me = self

    # WHEN preparing it
    result = prepare_data(Node())

    # THEN the cycle is cut instead of recursing forever
    assert isinstance(result["me"], Node)


def test_erase_object_referenced_twice_masks_both(data_masker):
    # GIVEN a plain object referenced twice and a rule on its field
    class Customer:
        def __init__(self, name):
            self.name = name

    customer = Customer("Pat")

    # WHEN erasing through masking rules
    result = data_masker.erase(
        {"payer": customer, "beneficiary": customer},
        masking_rules={"payer.name": {"dynamic_mask": True}, "beneficiary.name": {"dynamic_mask": True}},
    )

    # THEN both copies are masked
    assert result == {"payer": {"name": "***"}, "beneficiary": {"name": "***"}}


def test_prepare_data_object_without_attributes_is_returned_as_is():
    # GIVEN an object with neither __dict__ nor __slots__ attributes
    marker = object()

    # WHEN preparing it
    # THEN it is passed through unchanged, there is nothing to convert
    assert prepare_data(marker) is marker


def test_erase_regex_without_match_masks_whole_value(data_masker):
    # GIVEN a regex rule whose pattern does not match the value
    data = {"card": "no digits here"}

    # WHEN erasing with a pattern built for a different shape
    result = data_masker.erase(
        data,
        masking_rules={"card": {"regex_pattern": r"(\d{4})\d{8}(\d{4})", "mask_format": r"\1********\2"}},
    )

    # THEN the value is not handed back untouched, it is fully masked
    assert result == {"card": "** ****** ****"}


def test_erase_regex_with_match_keeps_format(data_masker):
    # GIVEN a regex rule whose pattern matches
    data = {"card": "1234567812345678"}

    # WHEN erasing
    result = data_masker.erase(
        data,
        masking_rules={"card": {"regex_pattern": r"(\d{4})\d{8}(\d{4})", "mask_format": r"\1********\2"}},
    )

    # THEN the format is applied
    assert result == {"card": "1234********5678"}


def test_erase_enum_value(data_masker):
    # GIVEN an Enum member as a value
    class Status(enum.Enum):
        ACTIVE = "active-token"

    data = {"status": Status.ACTIVE, "other": "keep"}

    # WHEN erasing the field
    result = data_masker.erase(data, fields=["status"])

    # THEN only the member value is considered and masked, no class internals leak into the output
    assert result == {"status": DATA_MASKING_STRING, "other": "keep"}
    assert prepare_data(data) == {"status": "active-token", "other": "keep"}
