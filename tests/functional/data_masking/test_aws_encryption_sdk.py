import pytest

from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from aws_lambda_powertools.utilities.data_masking.providers.aws_encryption_sdk import AwsEncryptionSdkProvider
from tests.unit.data_masking.setup import *

AWS_SDK_KEY = "arn:aws:kms:us-west-2:683517028648:key/269301eb-81eb-4067-ac72-98e8e49bf2b3"


@pytest.fixture
def data_masker():
    return DataMasking(provider=AwsEncryptionSdkProvider(keys=[AWS_SDK_KEY]))


@pytest.mark.parametrize("value, value_masked", data_types_and_masks)
def test_mask_types(value, value_masked, data_masker):
    # GIVEN any data type

    # WHEN the AWS encryption provider's mask method is called with no fields argument
    masked_string = data_masker.mask(value)

    # THEN the result is the full input data masked
    assert masked_string == value_masked


def test_mask_with_fields(data_masker):
    # GIVEN the data type is a dictionary, or a json representation of a dictionary

    # WHEN the AWS encryption provider's mask is called with a list of fields specified
    masked_string = data_masker.mask(python_dict, dict_fields)
    masked_json_string = data_masker.mask(json_dict, dict_fields)

    # THEN the result is only the specified fields are masked
    assert masked_string == masked_with_fields
    assert masked_json_string == masked_with_fields


@pytest.mark.parametrize("value", data_types)
def test_encrypt_decrypt(value, data_masker):
    # GIVEN an instantiation of DataMasking with the AWS encryption provider

    # WHEN encrypting and then decrypting the encrypted data
    encrypted_data = data_masker.encrypt(value)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == str(value)


@pytest.mark.parametrize("value, fields", zip(dictionaries, fields_to_mask))
def test_encrypt_decrypt_with_fields(value, fields, data_masker):
    # GIVEN an instantiation of DataMasking with the AWS encryption provider

    # WHEN encrypting and then decrypting the encrypted data with a list of fields
    encrypted_data = data_masker.encrypt(value, fields)
    decrypted_data = data_masker.decrypt(encrypted_data, fields)

    # THEN the result is the original input data
    # AWS Encryption SDK decrypt method only returns bytes
    print("value:", value)
    if value == json_blob:
        print("json blob!!!!")
        assert decrypted_data == value
    else:
        print("json_blob_fields!!!!")
        assert decrypted_data == str(value)
        print("decrypted_data:", decrypted_data)
        print("aws_encrypted_with_fields:", aws_encrypted_with_fields)
