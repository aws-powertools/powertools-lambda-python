import pytest

from aws_lambda_powertools.utilities.data_masking.exceptions import (
    DataMaskingContextMismatchError,
    DataMaskingUnsupportedTypeError,
)
from aws_lambda_powertools.utilities.data_masking.provider.kms.aws_encryption_sdk import (
    KMSKeyProvider,
)


def test_encryption_context_exact_match():
    ctx = {"data_classification": "confidential", "data_type": "customer_data"}
    ctx_two = {"data_type": "customer_data", "data_classification": "confidential"}

    KMSKeyProvider._compare_encryption_context(ctx, ctx_two)


def test_encryption_context_partial_match():
    ctx = {"data_classification": "confidential", "data_type": "customer_data"}
    ctx_two = {"data_type": "customer_data"}

    with pytest.raises(DataMaskingContextMismatchError):
        KMSKeyProvider._compare_encryption_context(ctx, ctx_two)


def test_encryption_context_supported_values():
    ctx = {"a": "b", "c": "d"}
    KMSKeyProvider._validate_encryption_context(ctx)
    KMSKeyProvider._validate_encryption_context({})


@pytest.mark.parametrize(
    "ctx",
    [
        pytest.param({"a": 10, "b": True, "c": []}, id="non_string_values"),
        pytest.param({"a": {"b": "c"}}, id="nested_dict"),
    ],
)
def test_encryption_context_non_str_validation(ctx):
    with pytest.raises(DataMaskingUnsupportedTypeError):
        KMSKeyProvider._validate_encryption_context(ctx)
