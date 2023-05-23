import json
import unittest

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


class TestDataMasking(unittest.TestCase):
    """Tests for sensitive data masking utility"""

    def __init__(self):
        super().__init__()
        self.python_dict = {
            "a": {
                "1": {"None": "hello", "four": "world"},  # None type key doesn't work
                "b": {"3": {"4": "goodbye", "e": "world"}},  # key "4.5" doesn't work
            }
        }
        self.json_dict = json.dumps(self.python_dict)
        self.fields = ["a.1.None", "a.b.3.4"]
        self.masked_with_fields = {
            "a": {"1": {"None": "*****", "four": "world"}, "b": {"3": {"4": "*****", "e": "world"}}}
        }

        self.list_of_data_types = [
            42,
            4.22,
            True,
            [1, 2, 3, 4],
            ["hello", 1, 2, 3, "world"],
            (55, 66, 88),
            None,
            "this is a string",
        ]
        self.list_of_data_types_masked = [
            "*****",
            "*****",
            "*****",
            ["*****", "*****", "*****", "*****"],
            ["*****", "*****", "*****", "*****", "*****"],
            ("*****", "*****", "*****"),
            "*****",
            "*****",
        ]

        # 10kb JSON blob for latency testing
        self.json_blob = {
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
        self.json_blob_fields = ["address.street", "job_history.company"]
        self.encrypted_list = []
        self.encrypted_data_python_dict = None
        self.encrypted_data_json_dict = None
        self.encrypted_data_python_dict_fields = None
        self.encrypted_data_json_dict_fields = None
        self.encrypted_json_blob = None

    def general_mask_test(self, data_masker):
        """Method to mask several different data types fully,
        and specific values in nested dicts"""
        # mask different data types fully
        for i, data_type in enumerate(self.list_of_data_types):
            masked_string = data_masker.mask(data_type)
            assert masked_string == self.list_of_data_types_masked[i]

        # mask dict fully
        masked_string = data_masker.mask(self.python_dict)
        assert masked_string == MASK
        masked_string = data_masker.mask(self.json_dict)
        assert masked_string == MASK

        # mask dict with fields
        masked_string = data_masker.mask(self.python_dict, self.fields)
        assert masked_string == self.masked_with_fields
        masked_string = data_masker.mask(self.json_dict, self.fields)
        assert masked_string == self.masked_with_fields

    def general_encrypt_test(self, data_masker):
        """Method to encrypt several different data types fully,
        and specific values in nested dicts"""
        # encrypt different data types fully
        self.encrypted_list = []
        for data_type in self.list_of_data_types:
            encrypted_data = data_masker.encrypt(data_type)
            self.encrypted_list.append(encrypted_data)

        # encrypt dict fully
        self.encrypted_data_python_dict = data_masker.encrypt(self.python_dict)
        self.encrypted_data_json_dict = data_masker.encrypt(self.json_dict)

        # encrypt dict with fields
        self.encrypted_data_python_dict_fields = data_masker.encrypt(self.python_dict, self.fields)
        self.encrypted_data_json_dict_fields = data_masker.encrypt(self.json_dict, self.fields)

        self.encrypted_json_blob = data_masker.encrypt(self.json_blob, self.json_blob_fields)

    def general_decrypt_test(self, data_masker):
        """Method to decrypt several different data types fully,
        and specific values in nested dicts"""
        # decrypt different data types fully
        for i, encrypted_data in enumerate(self.encrypted_list):
            decrypted_data = data_masker.decrypt(encrypted_data)
            # ie itsdangerous encrypts & decrypts tuples into type lists
            if decrypted_data == [55, 66, 88]:
                continue
            assert decrypted_data == self.list_of_data_types[i]

        # decrypt dict fully
        decrypted_data_python_dict = data_masker.decrypt(self.encrypted_data_python_dict)
        assert decrypted_data_python_dict == self.python_dict
        decrypted_data_json_dict = data_masker.decrypt(self.encrypted_data_json_dict)
        assert decrypted_data_json_dict == self.json_dict

        # decrypt dict with fields
        decrypted_data_python_dict_fields = data_masker.decrypt(self.encrypted_data_python_dict_fields, self.fields)
        assert decrypted_data_python_dict_fields == self.python_dict
        decrypted_data_json_dict_fields = data_masker.decrypt(self.encrypted_data_json_dict_fields, self.fields)
        assert decrypted_data_json_dict_fields == json.loads(self.json_dict)

        decrypted_json_blob = data_masker.decrypt(self.encrypted_json_blob, self.json_blob_fields)
        assert decrypted_json_blob == self.json_blob

    def test_mask(self):
        """Test masking with no Provider"""
        data_masker = DataMasking()
        self.general_mask_test(data_masker)

    def test_encrypt_not_implemented(self):
        """Test encrypting with no Provider"""
        data_masker = DataMasking()
        with pytest.raises(NotImplementedError):
            data_masker.encrypt("hello world")

    def test_decrypt_not_implemented(self):
        """Test decrypting with no Provider"""
        data_masker = DataMasking()
        with pytest.raises(NotImplementedError):
            data_masker.decrypt("hello world")

    def test_itsdangerous_mask(self):
        """Test masking with ItsDangerous provider"""
        itsdangerous_provider = ItsDangerousProvider("mykey")
        data_masker = DataMasking(provider=itsdangerous_provider)
        self.general_mask_test(data_masker)

    def test_itsdangerous_encrypt(self):
        """Test encrypting with ItsDangerous provider"""
        itsdangerous_provider = ItsDangerousProvider("mykey")
        data_masker = DataMasking(provider=itsdangerous_provider)

        # TypeError: type SET and BYTES is not JSON serializable, ie
        # itsdangerous for sets and bytes doesn't work
        self.general_encrypt_test(data_masker)

    def test_itsdangerous_decrypt(self):
        """Test decrypting with ItsDangerous provider"""
        itsdangerous_provider = ItsDangerousProvider("mykey")
        data_masker = DataMasking(provider=itsdangerous_provider)

        self.general_decrypt_test(data_masker)

    # TestCustomEncryptionSdkProvider
    def test_custom_mask(self):
        """Test masking with a custom encryption provider"""
        my_encryption = MyEncryptionProvider(keys="secret-key")
        data_masker = DataMasking(provider=my_encryption)
        self.general_mask_test(data_masker)

    def test_custom_encrypt(self):
        """Test encrypting with a custom encryption provider"""
        my_encryption = MyEncryptionProvider(keys="secret-key")
        data_masker = DataMasking(provider=my_encryption)

        # TypeError: type SET and BYTES is not JSON serializable ie.
        # itsdangerous for sets and bytes doesn't work
        self.general_encrypt_test(data_masker)

    def test_custom_decrypt(self):
        """Test decrypting with a custom encryption provider"""
        my_encryption = MyEncryptionProvider(keys="secret-key")
        data_masker = DataMasking(provider=my_encryption)

        self.general_decrypt_test(data_masker)

    # TestAwsEncryptionSdkProvider
    def test_awssdk_mask(self):
        """Test masking with AwsEncryptionSdk provider"""
        masking_provider = AwsEncryptionSdkProvider(keys=[AWS_SDK_KEY])
        data_masker = DataMasking(provider=masking_provider)
        self.general_mask_test(data_masker)

    def test_awssdk_encrypt(self):
        """Test encrypting with AwsEncryptionSdk provider"""
        masking_provider = AwsEncryptionSdkProvider(keys=[AWS_SDK_KEY])
        data_masker = DataMasking(provider=masking_provider)

        # AWS SDK encrypt method only takes in str | bytes, and returns bytes
        # May have to make a new list for this as some data types need to be utf-8 encoded
        # before being turned to bytes.
        # https://aws-encryption-sdk-python.readthedocs.io/en/latest/generated/aws_encryption_sdk.html

        self.encrypted_list = []
        for data_type in self.list_of_data_types:
            if isinstance(data_type, (str, bytes)):
                encrypted_data = data_masker.encrypt(data_type)
                self.encrypted_list.append(encrypted_data)

        # encrypt dict fully
        self.encrypted_data_json_dict = data_masker.encrypt(self.json_dict)

        # encrypt dict with fields
        self.encrypted_data_python_dict_fields = data_masker.encrypt(self.python_dict, self.fields)
        self.encrypted_data_json_dict_fields = data_masker.encrypt(self.json_dict, self.fields)

        self.encrypted_json_blob = data_masker.encrypt(json.dumps(self.json_blob), self.json_blob_fields)

    def test_awssdk_decrypt(self):
        """Test decrypting with AwsEncryptionSdk provider"""
        masking_provider = AwsEncryptionSdkProvider(keys=[AWS_SDK_KEY])
        data_masker = DataMasking(provider=masking_provider)

        # AWS SDK decrypt method returns only bytes
        # May have to make a new list for this as some data types need to be utf-8
        # encoded before being turned to bytes

        for i, encrypted_data in enumerate(self.encrypted_list):
            decrypted_data = data_masker.decrypt(encrypted_data)
            assert decrypted_data == self.list_of_data_types[i]

        decrypted_data_json_dict = data_masker.decrypt(self.encrypted_data_json_dict)
        assert decrypted_data_json_dict == bytes(self.json_dict, "utf-8")

        # AWS SDK encrypt method returning the individual fields decrypted as bytes
        decrypted_data_python_dict_fields = data_masker.decrypt(self.encrypted_data_python_dict_fields, self.fields)
        assert decrypted_data_python_dict_fields == self.python_dict

        # AWS SDK encrypt method returning the individual fields decrypted as bytes
        decrypted_data_json_dict_fields = data_masker.decrypt(self.encrypted_data_json_dict_fields, self.fields)
        assert decrypted_data_json_dict_fields == json.loads(self.json_dict)

        # AWS SDK encrypt method returning the individual fields decrypted as bytes
        decrypted_json_blob = data_masker.decrypt(self.encrypted_json_blob, self.json_blob_fields)
        assert decrypted_json_blob == self.json_blob
