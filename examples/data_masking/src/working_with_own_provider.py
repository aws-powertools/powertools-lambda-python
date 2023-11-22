from aws_lambda_powertools.utilities._data_masking.base import DataMasking
from examples.data_masking.src.custom_data_masking_provider import MyCustomEncryption


def lambda_handler(event, context):

    data = event["body"]

    encryption_provider = MyCustomEncryption(secret="secret-key")
    data_masker = DataMasking(provider=encryption_provider)

    encrypted = data_masker.encrypt(data, fields=["email", "address.street", "company_address"])

    data_masker.decrypt(data=encrypted, fields=["email", "address.street", "company_address"])
