import json
from uuid import uuid4
from aws_encryption_sdk.exceptions import DecryptKeyError
import pytest
from tests.e2e.utils import data_fetcher
from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from aws_lambda_powertools.utilities.data_masking.providers.aws_encryption_sdk import AwsEncryptionSdkProvider
from aws_lambda_powertools.shared.constants import DATA_MASKING_STRING


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
    value = bytes(str([1, 2, "string", 4.5]), "utf-8")

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(value)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == value


# TODO: Waiting on EncryptionSDK team to answer tt.amazon.com/V1005246120
@pytest.mark.xdist_group(name="data_masking")
def test_encryption_context(data_masker):
    # GIVEN an instantiation of DataMasking with the AWS encryption provider

    value = bytes(str([1, 2, "string", 4.5]), "utf-8")

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(value, encryption_context={"this": "is_secure"})
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == value


# TODO: metaclass?
@pytest.mark.xdist_group(name="data_masking")
def test_encryption_key_fail(kms_key2_arn, data_masker):
    # GIVEN an instantiation of DataMasking with the AWS encryption provider with a certain key

    # WHEN encrypting and then decrypting the encrypted data
    value = bytes(str([1, 2, "string", 4.5]), "utf-8")
    encrypted_data = data_masker.encrypt(value)

    data_masker_key2 = DataMasking(provider=AwsEncryptionSdkProvider(keys=[kms_key2_arn]))

    with pytest.raises(DecryptKeyError):
        data_masker_key2.decrypt(encrypted_data)


@pytest.mark.xdist_group(name="data_masking")
def test_masked_in_logs(basic_handler_fn, basic_handler_fn_arn):
    # GIVEN an instantiation of DataMasking with the AWS encryption provider
    data_masker = DataMasking(provider=AwsEncryptionSdkProvider(keys=[kms_key1_arn]))

    # WHEN masking a value and logging it
    masked_data = data_masker.mask([1, 2, "string", 4.5])
    message = masked_data
    custom_key = "order_id"
    additional_keys = {custom_key: f"{uuid4()}"}
    payload = json.dumps({"message": message, "append_keys": additional_keys})

    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn, payload=payload)
    data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn, payload=payload)

    # THEN the logs should show only the obfuscated data
    logs = data_fetcher.get_logs(function_name=basic_handler_fn, start_time=execution_time, minimum_log_entries=2)

    assert logs.have_keys("message") is True
