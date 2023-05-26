import json

import pytest
from itsdangerous.url_safe import URLSafeSerializer

from aws_lambda_powertools.shared.constants import DATA_MASKING_STRING as MASK
from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from aws_lambda_powertools.utilities.data_masking.provider import Provider
from aws_lambda_powertools.utilities.data_masking.providers.aws_encryption_sdk import (
    AwsEncryptionSdkProvider,
)
from aws_lambda_powertools.utilities.data_masking.providers.itsdangerous import (
    ItsDangerousProvider,
)

AWS_SDK_KEY = "arn:aws:kms:us-west-2:683517028648:key/269301eb-81eb-4067-ac72-98e8e49bf2b3"


class MyEncryptionProvider(Provider):
    """Custom encryption provider class"""

    def __init__(self, keys, salt=None):
        self.keys = keys
        self.salt = salt

    def encrypt(self, data: str) -> str:
        if data is None:
            return data
        serialize = URLSafeSerializer(self.keys)
        return serialize.dumps(data)

    def decrypt(self, data: str) -> str:
        if data is None:
            return data
        serialize = URLSafeSerializer(self.keys)
        return serialize.loads(data)


python_dict = {
    "a": {
        "1": {"None": "hello", "four": "world"},  # None type key doesn't work
        "b": {"3": {"4": "goodbye", "e": "world"}},  # key "4.5" doesn't work
    }
}
json_dict = json.dumps(python_dict)
fields = ["a.1.None", "a.b.3.4"]
masked_with_fields = {"a": {"1": {"None": MASK, "four": "world"}, "b": {"3": {"4": MASK, "e": "world"}}}}

# 10kb JSON blob for latency testing
json_blob = {
    "id": 1,
    "name": "John Doe",
    "age": 30,
    "email": "johndoe@example.com",
    "address": {"street": "123 Main St", "city": "Anytown", "state": "CA", "zip": "12345"},
    "phone_numbers": ["+1-555-555-1234", "+1-555-555-5678"],
    "interests": ["Hiking", "Traveling", "Photography", "Reading"],
    "job_history": {
        "company": "Acme Inc.",
        "position": "Software Engineer",
        "start_date": "2015-01-01",
        "end_date": "2017-12-31",
    },
    "about_me": """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla tincidunt velit quis
    sapien mollis, at egestas massa tincidunt. Suspendisse ultrices arcu a dolor dapibus,
    ut pretium turpis volutpat. Vestibulum at sapien quis sapien dignissim volutpat ut a enim.
    Praesent fringilla sem eu dui convallis luctus. Donec ullamcorper, sapien ut convallis congue,
    risus mauris pretium tortor, nec dignissim arcu urna a nisl. Vivamus non fermentum ex. Proin
    interdum nisi id sagittis egestas. Nam sit amet nisi nec quam pharetra sagittis. Aliquam erat
    volutpat. Donec nec luctus sem, nec ornare lorem. Vivamus vitae orci quis enim faucibus placerat. 
    Nulla facilisi. Proin in turpis orci. Donec imperdiet velit ac tellus gravida, eget laoreet tellus
    malesuada. Praesent venenatis tellus ac urna blandit, at varius felis posuere. Integer a commodo nunc.
    """,
}
json_blob_fields = ["address.street", "job_history.company"]

list_of_data_types = [
    # simple data types
    [42, MASK],
    [4.22, MASK],
    [True, MASK],
    [None, MASK],
    ["this is a string", MASK],
    # iterables
    [[1, 2, 3, 4], [MASK, MASK, MASK, MASK]],
    [["hello", 1, 2, 3, "world"], [MASK, MASK, MASK, MASK, MASK]],
    [(55, 66, 88), (MASK, MASK, MASK)],
    # dictionaries
    [python_dict, MASK],
    [json_dict, MASK],
]

list_of_data_maskers = [
    DataMasking(),
    DataMasking(provider=ItsDangerousProvider("mykey")),
    DataMasking(provider=AwsEncryptionSdkProvider(keys=[AWS_SDK_KEY])),
    DataMasking(provider=MyEncryptionProvider(keys="secret-key")),
]


@pytest.mark.parametrize("data_masker", list_of_data_maskers)
@pytest.mark.parametrize("value, value_masked", list_of_data_types)
def test_mask_types(data_masker, value, value_masked):
    """Method to mask a value"""
    masked_string = data_masker.mask(value)
    assert masked_string == value_masked


@pytest.mark.parametrize("data_masker", list_of_data_maskers)
def test_mask_with_fields(data_masker):
    # mask dict with fields
    masked_string = data_masker.mask(python_dict, fields)
    assert masked_string == masked_with_fields
    masked_string = data_masker.mask(json_dict, fields)
    assert masked_string == masked_with_fields


@pytest.mark.parametrize("data_masker", list_of_data_maskers)
@pytest.mark.parametrize("value", list_of_data_types)
def test_encrypt_decrypt(data_masker, value):
    """Method to encrypt several different data types fully,
    and specific values in nested dicts"""
    if data_masker == DataMasking():
        assert pytest.raises(NotImplementedError)

    # should raise error for no provider
    encrypted_data = data_masker.encrypt(value)
    decrypted_data = data_masker.decrypt(encrypted_data)
    assert decrypted_data == value


@pytest.mark.parametrize("data_masker", list_of_data_maskers)
@pytest.mark.parametrize("value", [python_dict, json_dict])
def test_encrypt_decrypt_with_fields(data_masker, value):
    encrypted_data = data_masker.encrypt(value, fields)
    decrypted_data = data_masker.decrypt(encrypted_data, fields)
    if decrypted_data == [55, 66, 88]:
        pytest.skip()
    assert decrypted_data == value

    encrypted_json_blob = data_masker.encrypt(json_blob, json_blob_fields)
    decrypted_json_blob = data_masker.decrypt(encrypted_json_blob, json_blob_fields)
    assert decrypted_json_blob == json_blob


def test_encrypt_not_implemented():
    """Test encrypting with no Provider"""
    data_masker = DataMasking()
    with pytest.raises(NotImplementedError):
        data_masker.encrypt("hello world")


def test_decrypt_not_implemented():
    """Test decrypting with no Provider"""
    data_masker = DataMasking()
    with pytest.raises(NotImplementedError):
        data_masker.decrypt("hello world")
