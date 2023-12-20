import pytest

from aws_lambda_powertools.utilities._data_masking.exceptions import DataMaskingContextMismatchError
from aws_lambda_powertools.utilities._data_masking.provider.kms.aws_encryption_sdk import (
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
