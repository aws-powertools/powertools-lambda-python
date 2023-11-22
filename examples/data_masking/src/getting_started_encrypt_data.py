import os

from aws_lambda_powertools.utilities._data_masking import DataMasking
from aws_lambda_powertools.utilities._data_masking.provider.kms.aws_encryption_sdk import AwsEncryptionSdkProvider

KMS_KEY_ARN = os.getenv("KMS_KEY_ARN")

def lambda_handler(event, context):

    data = event["body"]

    encryption_provider = AwsEncryptionSdkProvider(keys=[KMS_KEY_ARN])
    data_masker = DataMasking(provider=encryption_provider)

    encrypted = data_masker.encrypt(data=data, fields=["email", "address.street", "company_address"])

    data_masker.decrypt(data=encrypted, fields=["email", "address.street", "company_address"])
