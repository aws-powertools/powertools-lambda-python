import os

from aws_lambda_powertools.utilities._data_masking import DataMasking
from aws_lambda_powertools.utilities._data_masking.provider.kms.aws_encryption_sdk import AwsEncryptionSdkProvider

KMS_KEY_ARN = os.environ["KMS_KEY_ARN"]

def lambda_handler(event, context):

    data = {
        "id": 1,
        "name": "John Doe",
        "age": 30,
        "email": "johndoe@example.com",
        "address": {
            "street": "123 Main St", 
            "city": "Anytown", 
            "state": "CA", 
            "zip": "12345",
        },
        "company_address": {
            "street": "456 ACME Ave", 
            "city": "Anytown", 
            "state": "CA", 
            "zip": "12345",
        },
    }

    encryption_provider = AwsEncryptionSdkProvider(keys=[KMS_KEY_ARN])
    data_masker = DataMasking(provider=encryption_provider)

    encrypted = data_masker.encrypt(data=data, fields=["email", "address.street", "company_address"])

    data_masker.decrypt(data=encrypted, fields=["email", "address.street", "company_address"])
