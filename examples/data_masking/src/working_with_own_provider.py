from aws_lambda_powertools.utilities._data_masking.base import DataMasking
from examples.data_masking.src.custom_provider import MyCustomEncryption


def lambda_handler():
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

    encryption_provider = MyCustomEncryption(secret="secret-key")
    data_masker = DataMasking(provider=encryption_provider)

    encrypted = data_masker.encrypt(data, fields=["email", "address.street", "company_address"])

    data_masker.decrypt(data=encrypted, fields=["email", "address.street", "company_address"])
