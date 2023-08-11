import json
import pytest
from itsdangerous.url_safe import URLSafeSerializer
from aws_lambda_powertools.shared.constants import DATA_MASKING_STRING
from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from aws_lambda_powertools.utilities.data_masking.provider import Provider


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


# @pytest.fixture
# def data_masker():
#     return DataMasking()


# @pytest.fixture
# def custom_data_masker():
#     return DataMasking(provider=MyEncryptionProvider(keys="secret-key"))


def test_mask_int():
    data_masker = DataMasking()

    # GIVEN an int data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask(42)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_float():
    data_masker = DataMasking()

    # GIVEN a float data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask(4.2)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_bool():
    data_masker = DataMasking()

    # GIVEN a bool data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask(True)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_none():
    data_masker = DataMasking()

    # GIVEN a None data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask(None)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_str():
    data_masker = DataMasking()

    # GIVEN a str data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask("this is a string")

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_list():
    data_masker = DataMasking()

    # GIVEN a list data type

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask([1, 2, "string", 3])

    # THEN the result is the data masked, while maintaining type list
    assert masked_string == [DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING]


def test_mask_dict():
    data_masker = DataMasking()

    # GIVEN a dict data type
    data = {
        "a": {
            "1": {"None": "hello", "four": "world"},
            "b": {"3": {"4": "goodbye", "e": "world"}},
        }
    }

    # WHEN mask is called with no fields argument
    masked_string = data_masker.mask(data)

    # THEN the result is the data masked
    assert masked_string == DATA_MASKING_STRING


def test_mask_dict_with_fields():
    data_masker = DataMasking()

    # GIVEN the data type is a dictionary
    data = {
        "a": {
            "1": {"None": "hello", "four": "world"},
            "b": {"3": {"4": "goodbye", "e": "world"}},
        }
    }

    # WHEN mask is called with a list of fields specified
    masked_string = data_masker.mask(data, fields=["a.1.None", "a.b.3.4"])

    # THEN the result is only the specified fields are masked
    assert masked_string == {
        "a": {"1": {"None": DATA_MASKING_STRING, "four": "world"}, "b": {"3": {"4": DATA_MASKING_STRING, "e": "world"}}}
    }


def test_mask_json_dict_with_fields():
    data_masker = DataMasking()

    # GIVEN the data type is a json representation of a dictionary
    data = json.dumps(
        {
            "a": {
                "1": {"None": "hello", "four": "world"},
                "b": {"3": {"4": "goodbye", "e": "world"}},
            }
        }
    )

    # WHEN mask is called with a list of fields specified
    masked_json_string = data_masker.mask(data, fields=["a.1.None", "a.b.3.4"])

    # THEN the result is only the specified fields are masked
    assert masked_json_string == {
        "a": {"1": {"None": DATA_MASKING_STRING, "four": "world"}, "b": {"3": {"4": DATA_MASKING_STRING, "e": "world"}}}
    }


def test_encrypt_decrypt_int():
    # GIVEN an instantiation of DataMasking with a Provider
    data_masker = DataMasking(provider=MyEncryptionProvider(keys="secret-key"))

    # WHEN encrypting and then decrypting an int
    encrypted_data = data_masker.encrypt(42)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == 42


def test_encrypt_decrypt_float():
    # GIVEN an instantiation of DataMasking with a Provider
    data_masker = DataMasking(provider=MyEncryptionProvider(keys="secret-key"))

    # WHEN encrypting and then decrypting a float
    encrypted_data = data_masker.encrypt(4.2)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == 4.2


def test_encrypt_decrypt_bool():
    # GIVEN an instantiation of DataMasking with a Provider
    data_masker = DataMasking(provider=MyEncryptionProvider(keys="secret-key"))

    # WHEN encrypting and then decrypting a bool
    encrypted_data = data_masker.encrypt(True)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == True


def test_encrypt_decrypt_none():
    # GIVEN an instantiation of DataMasking with a Provider
    data_masker = DataMasking(provider=MyEncryptionProvider(keys="secret-key"))

    # WHEN encrypting and then decrypting a None type
    encrypted_data = data_masker.encrypt(None)
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == None


def test_encrypt_decrypt_str():
    # GIVEN an instantiation of DataMasking with a Provider
    data_masker = DataMasking(provider=MyEncryptionProvider(keys="secret-key"))

    # WHEN encrypting and then decrypting a string
    encrypted_data = data_masker.encrypt("this is a string")
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == "this is a string"


def test_encrypt_decrypt_list():
    # GIVEN an instantiation of DataMasking with a Provider
    data_masker = DataMasking(provider=MyEncryptionProvider(keys="secret-key"))

    # WHEN encrypting and then decrypting a list
    encrypted_data = data_masker.encrypt([1, 2, "string", 4])
    decrypted_data = data_masker.decrypt(encrypted_data)

    # THEN the result is the original input data
    assert decrypted_data == [1, 2, "string", 4]


def test_dict_encryption_with_fields():
    # GIVEN an instantiation of DataMasking with a Provider
    data_masker = DataMasking(provider=MyEncryptionProvider(keys="secret-key"))

    data = {
        "a": {
            "1": {"None": "hello", "four": "world"},
            "b": {"3": {"4": "goodbye", "e": "world"}},
        }
    }

    # WHEN encrypting and decrypting the data with a list of fields
    encrypted_data = data_masker.encrypt(data, fields=["a.1.None", "a.b.3.4"])
    decrypted_data = data_masker.decrypt(encrypted_data, fields=["a.1.None", "a.b.3.4"])

    # THEN the result is the original input data
    assert decrypted_data == data


def test_json_encryption_with_fields():
    # GIVEN an instantiation of DataMasking with a Provider
    data_masker = DataMasking(provider=MyEncryptionProvider(keys="secret-key"))

    data = json.dumps(
        {
            "a": {
                "1": {"None": "hello", "four": "world"},
                "b": {"3": {"4": "goodbye", "e": "world"}},
            }
        }
    )

    # WHEN encrypting and decrypting a json representation of a dictionary with a list of fields
    encrypted_data = data_masker.encrypt(data, fields=["a.1.None", "a.b.3.4"])
    decrypted_data = data_masker.decrypt(encrypted_data, fields=["a.1.None", "a.b.3.4"])

    # THEN the result is the original input data
    assert decrypted_data == json.loads(data)


def test_big_data_encryption_with_fields():
    # GIVEN an instantiation of DataMasking with a Provider
    data_masker = DataMasking(provider=MyEncryptionProvider(keys="secret-key"))

    # 10kb JSON blob for latency testing
    data = {
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

    # WHEN encrypting and decrypting the data with a list of fields
    encrypted_data = data_masker.encrypt(data, fields=["address.street", "job_history.company"])
    decrypted_data = data_masker.decrypt(encrypted_data, fields=["address.street", "job_history.company"])

    # THEN the result is the original input data
    assert decrypted_data == data


def test_encrypt_not_implemented():
    # GIVEN DataMasking is not initialized with a Provider
    data_masker = DataMasking()

    # WHEN attempting to call the encrypt method on the data

    # THEN the result is a NotImplementedError
    with pytest.raises(NotImplementedError):
        data_masker.encrypt("hello world")


def test_decrypt_not_implemented():
    # GIVEN DataMasking is not initialized with a Provider
    data_masker = DataMasking()

    # WHEN attempting to call the decrypt method on the data

    # THEN the result is a NotImplementedError
    with pytest.raises(NotImplementedError):
        data_masker.decrypt("hello world")


def test_parsing_unsupported_data_type():
    # GIVEN an initialization of the DataMasking class
    data_masker = DataMasking()

    # WHEN attempting to pass in a list of fields with input data that is not a dict

    # THEN the result is a TypeError
    with pytest.raises(TypeError):
        data_masker.mask(42, ["this.field"])


def test_parsing_nonexistent_fields():
    # GIVEN an initialization of the DataMasking class
    data_masker = DataMasking()
    data = {
        "3": {
            "1": {"None": "hello", "four": "world"},
            "4": {"33": {"5": "goodbye", "e": "world"}},
        }
    }

    # WHEN attempting to pass in fields that do not exist in the input data

    # THEN the result is a KeyError
    with pytest.raises(KeyError):
        data_masker.mask(data, ["3.1.True"])


def test_parsing_nonstring_fields():
    # GIVEN an initialization of the DataMasking class
    data_masker = DataMasking()
    data = {
        "3": {
            "1": {"None": "hello", "four": "world"},
            "4": {"33": {"5": "goodbye", "e": "world"}},
        }
    }

    # WHEN attempting to pass in a list of fields that are not strings
    masked = data_masker.mask(data, fields=[3.4])

    # THEN the result is the value of the nested field should be masked as normal
    assert masked == {"3": {"1": {"None": "hello", "four": "world"}, "4": DATA_MASKING_STRING}}


def test_parsing_nonstring_keys_and_fields():
    # GIVEN an initialization of the DataMasking class
    data_masker = DataMasking()

    # WHEN the input data is a dictionary with integer keys
    data = {
        3: {
            "1": {"None": "hello", "four": "world"},
            4: {"33": {"5": "goodbye", "e": "world"}},
        }
    }
    masked = data_masker.mask(data, fields=[3.4])

    # THEN the result is the value of the nested field should be masked as normal
    assert masked == {"3": {"1": {"None": "hello", "four": "world"}, "4": DATA_MASKING_STRING}}
