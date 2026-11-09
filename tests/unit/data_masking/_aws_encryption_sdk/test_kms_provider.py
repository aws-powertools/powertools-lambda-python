from __future__ import annotations

import pytest
from aws_encryption_sdk.exceptions import MasterKeyProviderError, SerializationError
from cryptography.exceptions import InvalidSignature

from aws_lambda_powertools.utilities.data_masking.exceptions import (
    DataMaskingContextMismatchError,
    DataMaskingDecryptValueError,
    DataMaskingUnsupportedTypeError,
)
from aws_lambda_powertools.utilities.data_masking.provider.kms.aws_encryption_sdk import (
    AWSEncryptionSDKProvider,
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


@pytest.mark.parametrize(
    "sdk_error",
    [
        InvalidSignature(),
        SerializationError("truncated"),
        ValueError("bad header"),
        MasterKeyProviderError("Key commitment validation failed"),
    ],
    ids=["tampered", "truncated", "garbage", "key_commitment"],
)
def test_decrypt_wraps_sdk_errors(monkeypatch, sdk_error):
    # GIVEN a provider whose SDK client rejects the ciphertext
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    provider = AWSEncryptionSDKProvider(keys=["arn:aws:kms:us-east-1:111122223333:key/test"])

    def failing_decrypt(**kwargs):
        raise sdk_error

    monkeypatch.setattr(provider._key_provider.client, "decrypt", failing_decrypt)

    # WHEN decrypting a well-formed base64 payload
    # THEN the failure is reported as DataMaskingDecryptValueError, not as the SDK's own exception
    with pytest.raises(DataMaskingDecryptValueError):
        provider.decrypt("QUJDRA==")


def test_decrypt_rejects_non_base64_input(monkeypatch):
    # GIVEN a provider
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    provider = AWSEncryptionSDKProvider(keys=["arn:aws:kms:us-east-1:111122223333:key/test"])

    # WHEN decrypting something that is not base64
    # THEN it is a DataMaskingDecryptValueError, not a raw ValueError
    with pytest.raises(DataMaskingDecryptValueError):
        provider.decrypt("not base64 at all!!")
