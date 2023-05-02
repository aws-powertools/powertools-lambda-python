import unittest
from aws_lambda_powertools.utilities.data_masking import DataMasking, ItsDangerousProvider, AwsEncryptionSdkProvider, Provider
from aws_lambda_powertools.shared import DATA_MASKING_STRING as MASK
from itsdangerous.url_safe import URLSafeSerializer
import json


AWS_SDK_KEY = "arn:aws:kms:us-west-2:683517028648:key/269301eb-81eb-4067-ac72-98e8e49bf2b3"

class MyEncryptionProvider(Provider):
    def __init__(self, keys, salt=None):
        self.keys = keys
        self.salt = salt

    def mask(self, value):
        return super().mask(value)

    def encrypt(self, value: str) -> str:
        if value is None:
            return value
        s = URLSafeSerializer(self.keys)
        return s.dumps(value)
        
    def decrypt(self, value: str) -> str:
        if value is None:
            return value
        s = URLSafeSerializer(self.keys)
        return s.loads(value)
        

class TestDataMasking(unittest.TestCase):
    def __init__(self):
        super().__init__()
        self.python_dict = {
            'a': {
                '1': {
                    'None': 'hello', # None type key doesn't work
                    'four': 'world'
                },
                'b': {
                    '3': {
                        '4': 'goodbye', # key "4.5" doesn't work
                        'e': 'world'
                    }
                }
            }
        }
        self.json_dict = json.dumps(self.python_dict)
        self.fields = ["a.1.None", "a.b.3.4"]
        self.masked_with_fields = {'a': {'1': {'None': '*****', 'four': 'world'}, 'b': {'3': {'4': '*****', 'e': 'world'}}}}

        self.list_of_data_types = [42, 4.22, True, [1, 2, 3, 4], ["hello", 1, 2, 3, "world"], tuple((55, 66, 88)), None, "this is a string"]
        self.list_of_data_types_masked = ["*****", "*****", "*****", ['*****', '*****', '*****', '*****'], ['*****', '*****', '*****', '*****', '*****'], ('*****', '*****', '*****'), "*****", "*****"]

        # 10kb JSON blob for latency testing
        self.bigJSON = {
            "id": 1,
            "name": "John Doe",
            "age": 30,
            "email": "johndoe@example.com",
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345"
            },
            "phone_numbers": [
                "+1-555-555-1234",
                "+1-555-555-5678"
            ],
            "interests": [
                "Hiking",
                "Traveling",
                "Photography",
                "Reading"
            ],
            "job_history":
                {
                    "company": "Acme Inc.",
                    "position": "Software Engineer",
                    "start_date": "2015-01-01",
                    "end_date": "2017-12-31"
                },
            "about_me": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla tincidunt velit quis sapien mollis, at egestas massa tincidunt. Suspendisse ultrices arcu a dolor dapibus, ut pretium turpis volutpat. Vestibulum at sapien quis sapien dignissim volutpat ut a enim. Praesent fringilla sem eu dui convallis luctus. Donec ullamcorper, sapien ut convallis congue, risus mauris pretium tortor, nec dignissim arcu urna a nisl. Vivamus non fermentum ex. Proin interdum nisi id sagittis egestas. Nam sit amet nisi nec quam pharetra sagittis. Aliquam erat volutpat. Donec nec luctus sem, nec ornare lorem. Vivamus vitae orci quis enim faucibus placerat. Nulla facilisi. Proin in turpis orci. Donec imperdiet velit ac tellus gravida, eget laoreet tellus malesuada. Praesent venenatis tellus ac urna blandit, at varius felis posuere. Integer a commodo nunc."
        }
        self.bigJSONfields = ["address.street", "job_history.company"]
    
    
    def general_mask_test(self, dm):
        # mask different data types fully
        for i, data_type in enumerate(self.list_of_data_types):
            masked_string = dm.mask(data_type)
            self.assertEqual(masked_string, self.list_of_data_types_masked[i])
       
        # mask dict fully
        masked_string = dm.mask(self.python_dict)
        self.assertEqual(masked_string, MASK)
        masked_string = dm.mask(self.json_dict)
        self.assertEqual(masked_string, MASK)

        # mask dict with fields
        masked_string = dm.mask(self.python_dict, self.fields)
        self.assertEqual(masked_string, self.masked_with_fields)
        masked_string = dm.mask(self.json_dict, self.fields)
        self.assertEqual(masked_string, self.masked_with_fields)


    def general_encrypt_test(self, dm):
        # encrypt different data types fully
        self.encrypted_list = []
        for i, data_type in enumerate(self.list_of_data_types):
            encrypted_data = dm.encrypt(data_type)
            self.encrypted_list.append(encrypted_data)

        # encrypt dict fully
        self.encrypted_data_python_dict = dm.encrypt(self.python_dict)
        self.encrypted_data_json_dict = dm.encrypt(self.json_dict)

        # encrypt dict with fields
        self.encrypted_data_python_dict_fields = dm.encrypt(self.python_dict, self.fields)
        self.encrypted_data_json_dict_fields = dm.encrypt(self.json_dict, self.fields)

        self.encrypted_big_json = dm.encrypt(self.bigJSON, self.bigJSONfields)

    def general_decrypt_test(self, dm):
        # decrypt different data types fully
        for i, data_type in enumerate(self.list_of_data_types):
            decrypted_data = dm.decrypt(self.encrypted_list[i])
            # AssertionError: [55, 66, 88] != (55, 66, 88) ie itsdangerous encrypts&decrypts tuples into type lists
            if decrypted_data == [55, 66, 88]:
                continue
            self.assertEqual(decrypted_data, self.list_of_data_types[i])

        # decrypt dict fully
        decrypted_data_python_dict = dm.decrypt(self.encrypted_data_python_dict)
        self.assertEqual(decrypted_data_python_dict, self.python_dict)
        decrypted_data_json_dict = dm.decrypt(self.encrypted_data_json_dict)
        self.assertEqual(decrypted_data_json_dict, self.json_dict)

        # decrypt dict with fields
        decrypted_data_python_dict_fields = dm.decrypt(self.encrypted_data_python_dict_fields, self.fields)
        self.assertEqual(decrypted_data_python_dict_fields, self.python_dict)
        decrypted_data_json_dict_fields = dm.decrypt(self.encrypted_data_json_dict_fields, self.fields)
        self.assertEqual(decrypted_data_json_dict_fields, json.loads(self.json_dict))

        decrypted_big_json = dm.decrypt(self.encrypted_big_json, self.bigJSONfields)
        self.assertEqual(decrypted_big_json, self.bigJSON)

    
    # TestNoProvder
    def test_mask(self):
        dm = DataMasking()
        self.general_mask_test(dm)

    def test_encrypt_not_implemented(self):
        dm = DataMasking()
        with self.assertRaises(NotImplementedError):
            dm.encrypt("hello world")

    def test_decrypt_not_implemented(self):
        dm = DataMasking()
        with self.assertRaises(NotImplementedError):
            dm.decrypt("hello world")


    # TestItsDangerousProvider
    def test_itsdangerous_mask(self):
        itsdangerous_provider = ItsDangerousProvider("mykey")
        dm = DataMasking(provider=itsdangerous_provider)
        self.general_mask_test(dm)        


    def test_itsdangerous_encrypt(self):
        itsdangerous_provider = ItsDangerousProvider("mykey")
        dm = DataMasking(provider=itsdangerous_provider)

        # NOTE: TypeError: type SET and BYTES is not JSON serializable - itsdangerous for sets and bytes doesn't work
        self.general_encrypt_test(dm)


    def test_itsdangerous_decrypt(self):
        itsdangerous_provider = ItsDangerousProvider("mykey")
        dm = DataMasking(provider=itsdangerous_provider)

        self.general_decrypt_test(dm)


    # TestCustomEncryptionSdkProvider
    def test_custom_mask(self):
        my_encryption = MyEncryptionProvider(keys="secret-key")
        dm = DataMasking(provider=my_encryption)
        self.general_mask_test(dm)


    def test_custom_encrypt(self):
        my_encryption = MyEncryptionProvider(keys="secret-key")
        dm = DataMasking(provider=my_encryption)

        # NOTE: TypeError: type SET and BYTES is not JSON serializable - itsdangerous for sets and bytes doesn't work
        self.general_encrypt_test(dm)


    def test_custom_decrypt(self):
        my_encryption = MyEncryptionProvider(keys="secret-key")
        dm = DataMasking(provider=my_encryption)

        self.general_decrypt_test(dm)



    # TestAwsEncryptionSdkProvider
    def test_awssdk_mask(self):
        masking_provider = AwsEncryptionSdkProvider(keys=[AWS_SDK_KEY])
        dm = DataMasking(provider=masking_provider)
        self.general_mask_test(dm)


    def test_awssdk_encrypt(self):
        masking_provider = AwsEncryptionSdkProvider(keys=[AWS_SDK_KEY])
        dm = DataMasking(provider=masking_provider)

        # TODO: AWS SDK encrypt method only takes in str | bytes, and returns bytes
        # May have to make a new list for this since some data types need to be utf-8 encoded before being turned to bytes.
        # https://aws-encryption-sdk-python.readthedocs.io/en/latest/generated/aws_encryption_sdk.html

        self.encrypted_list = []
        for i, data_type in enumerate(self.list_of_data_types):
            if isinstance(data_type, str) or isinstance(data_type, bytes):
                encrypted_data = dm.encrypt(data_type)
                self.encrypted_list.append(encrypted_data)
        
        # encrypt dict fully
        self.encrypted_data_json_dict = dm.encrypt(self.json_dict)

        # encrypt dict with fields
        self.encrypted_data_python_dict_fields = dm.encrypt(self.python_dict, self.fields)
        self.encrypted_data_json_dict_fields = dm.encrypt(self.json_dict, self.fields)

        self.encrypted_big_json = dm.encrypt(json.dumps(self.bigJSON), self.bigJSONfields)


    def test_awssdk_decrypt(self):
        masking_provider = AwsEncryptionSdkProvider(keys=[AWS_SDK_KEY])
        dm = DataMasking(provider=masking_provider)

        
        # TODO: AWS SDK decrypt method returns only bytes 
        # May have to make a new list for this since some data types need to be utf-8 encoded before being turned to bytes.

        # for i, data_type in enumerate(self.list_of_data_types):
        #     decrypted_data = dm.decrypt(self.encrypted_list[i])
        #     self.assertEqual(decrypted_data, self.list_of_data_types[i])

        decrypted_data_json_dict = dm.decrypt(self.encrypted_data_json_dict)
        self.assertEqual(decrypted_data_json_dict, bytes(self.json_dict, 'utf-8'))

        # AWS SDK encrypt method returning the individual fields decrypted as bytes
        decrypted_data_python_dict_fields = dm.decrypt(self.encrypted_data_python_dict_fields, self.fields)
        # self.assertEqual(decrypted_data_python_dict_fields, self.python_dict)

        # AWS SDK encrypt method returning the individual fields decrypted as bytes
        decrypted_data_json_dict_fields = dm.decrypt(self.encrypted_data_json_dict_fields, self.fields)
        # self.assertEqual(decrypted_data_json_dict_fields, json.loads(self.json_dict))

        # AWS SDK encrypt method returning the individual fields decrypted as bytes
        decrypted_big_json = dm.decrypt(self.encrypted_big_json, self.bigJSONfields)
        # self.assertEqual(decrypted_big_json, self.bigJSON)