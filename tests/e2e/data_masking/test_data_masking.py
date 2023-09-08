import json
from uuid import uuid4

import pytest
from aws_encryption_sdk.exceptions import DecryptKeyError

from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from aws_lambda_powertools.utilities.data_masking.providers.aws_encryption_sdk import (
    AwsEncryptionSdkProvider,
    ContextMismatchError,
)
from tests.e2e.utils import data_fetcher


@pytest.fixture
def basic_handler_fn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandler", "")


@pytest.fixture
def basic_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandlerArn", "")


@pytest.fixture
def kms_key1_arn(infrastructure: dict) -> str:
    return infrastructure.get("KMSKey1Arn", "")


@pytest.fixture
def kms_key2_arn(infrastructure: dict) -> str:
    return infrastructure.get("KMSKey2Arn", "")


@pytest.fixture
def data_masker(kms_key1_arn) -> DataMasking:
    return DataMasking(provider=AwsEncryptionSdkProvider(keys=[kms_key1_arn]))


@pytest.mark.xdist_group(name="data_masking")
def test_encryption(data_masker):
    # GIVEN an instantiation of DataMasking with the AWS encryption provider

    # AWS Encryption SDK encrypt method only takes in bytes or strings
    value = [1, 2, "string", 4.5]

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(value)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == str(value)


@pytest.mark.xdist_group(name="data_masking")
def test_encryption_context(data_masker):
    # GIVEN an instantiation of DataMasking with the AWS encryption provider

    value = [1, 2, "string", 4.5]
    context = {"this": "is_secure"}

    # WHEN encrypting and then decrypting the encrypted data with an encryption_context
    encrypted_data = data_masker.encrypt(value, encryption_context=context)
    decrypted_data = data_masker.decrypt(encrypted_data, encryption_context=context)

    # THEN the result is the original input data
    assert decrypted_data == str(value)


@pytest.mark.xdist_group(name="data_masking")
def test_encryption_context_mismatch(data_masker):
    # GIVEN an instantiation of DataMasking with the AWS encryption provider

    value = [1, 2, "string", 4.5]

    # WHEN encrypting with a encryption_context
    encrypted_data = data_masker.encrypt(value, encryption_context={"this": "is_secure"})

    # THEN decrypting with a different encryption_context should raise a ContextMismatchError
    with pytest.raises(ContextMismatchError):
        data_masker.decrypt(encrypted_data, encryption_context={"not": "same_context"})


@pytest.mark.xdist_group(name="data_masking")
def test_encryption_no_context_fail(data_masker):
    # GIVEN an instantiation of DataMasking with the AWS encryption provider

    value = [1, 2, "string", 4.5]

    # WHEN encrypting with no encryption_context
    encrypted_data = data_masker.encrypt(value)

    # THEN decrypting with an encryption_context should raise a ContextMismatchError
    with pytest.raises(ContextMismatchError):
        data_masker.decrypt(encrypted_data, encryption_context={"this": "is_secure"})


@pytest.mark.xdist_group(name="data_masking")
def test_encryption_decryption_key_mismatch(data_masker, kms_key2_arn):
    # GIVEN an instantiation of DataMasking with the AWS encryption provider with a certain key

    # WHEN encrypting and then decrypting the encrypted data
    value = [1, 2, "string", 4.5]
    encrypted_data = data_masker.encrypt(value)

    # THEN when decrypting with a different key it should fail
    data_masker_key2 = DataMasking(provider=AwsEncryptionSdkProvider(keys=[kms_key2_arn]))

    with pytest.raises(DecryptKeyError):
        data_masker_key2.decrypt(encrypted_data)


def test_encryption_provider_singleton(data_masker, kms_key1_arn, kms_key2_arn):
    data_masker_2 = DataMasking(provider=AwsEncryptionSdkProvider(keys=[kms_key1_arn]))
    assert data_masker.provider is data_masker_2.provider

    value = [1, 2, "string", 4.5]

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(value)
    decrypted_data = data_masker_2.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == str(value)

    data_masker_3 = DataMasking(provider=AwsEncryptionSdkProvider(keys=[kms_key2_arn]))
    assert data_masker_2.provider is not data_masker_3.provider


@pytest.mark.xdist_group(name="data_masking")
def test_encryption_in_logs(data_masker, basic_handler_fn, basic_handler_fn_arn):
    # GIVEN an instantiation of DataMasking with the AWS encryption provider

    # WHEN encrypting a value and logging it
    value = [1, 2, "string", 4.5]
    encrypted_data = data_masker.encrypt(value)
    message = encrypted_data
    custom_key = "order_id"
    additional_keys = {custom_key: f"{uuid4()}"}
    payload = json.dumps({"message": message, "append_keys": additional_keys})

    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn, payload=payload)
    data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn, payload=payload)

    logs = data_fetcher.get_logs(function_name=basic_handler_fn, start_time=execution_time, minimum_log_entries=2)

    # THEN decrypting it from the logs should show the original value
    for log in logs.get_log(key=custom_key):
        encrypted_data = log.message
        decrypted_data = data_masker.decrypt(encrypted_data)
        assert decrypted_data == str(value)


# NOTE: This test is failing currently, need to find a fix for building correct dependencies
@pytest.mark.xdist_group(name="data_masking")
def test_encryption_in_handler(basic_handler_fn_arn, kms_key1_arn):
    payload = {"kms_key": kms_key1_arn, "append_keys": {"order_id": f"{uuid4()}"}}

    # WHEN a lambda handler for encryption is invoked
    handler_result, _ = data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn, payload=json.dumps(payload))

    response = json.loads(handler_result["Payload"].read())
    encrypted_data = response["encrypted_data"]
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN decrypting the encrypted data from the response should result in the original value
    assert decrypted_data == str([1, 2, "string", 4.5])
