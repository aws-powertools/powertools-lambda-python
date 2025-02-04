import pytest

from aws_lambda_powertools.utilities.data_masking.base import DataMasking


@pytest.fixture
def data_masker() -> DataMasking:
    return DataMasking()


def test_mask_nested_field_with_non_dict_value(data_masker):
    # GIVEN nested data where a middle path component is not a dictionary
    data = {"user": {"contact": "not_a_dict", "details": {"ssn": "123-45-6789"}}}  # This will stop the traversal

    # WHEN attempting to mask a field through a path containing a non-dict value
    data_masker._mask_nested_field(data, "user.contact.details.ssn", lambda x: "MASKED")

    # THEN the data should remain unchanged since traversal stopped at non-dict value
    assert data == {"user": {"contact": "not_a_dict", "details": {"ssn": "123-45-6789"}}}


def test_mask_nested_field_success(data_masker):
    # GIVEN nested data with a field to mask
    data = {"user": {"contact": {"details": {"address": {"street": "123 Main St", "zip": "12345"}}}}}

    # WHEN masking a nested field with a masking rule
    data_masker._mask_nested_field(data, "user.contact.details.address.zip", {"custom_mask": "xxx"})

    # THEN the nested field should be masked while other data remains unchanged
    assert data == {"user": {"contact": {"details": {"address": {"street": "123 Main St", "zip": "xxx"}}}}}
