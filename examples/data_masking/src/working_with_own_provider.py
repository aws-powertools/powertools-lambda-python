from aws_lambda_powertools.utilities.data_masking.base import DataMasking
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
    }

    encryption_provider = MyCustomEncryption(secret="secret-key")
    data_masker = DataMasking(provider=encryption_provider)

    encrypted = data_masker.encrypt(data, fields=["email", "address.street"])
    # encrypted = {
    #     "id": 1,
    #     "name": "John Doe",
    #     "age": 30,
    #     "email": "InRoaXMgaXMgYSBzdHJpbmciHsLZGx2na-XzP_TB5Bf2LNU1bLc",
    #     "address": {
    #         "street": "XMgYSB_KDddaDJYMb-JpbmGnagTklwQ-msdaDLP",
    #         "city": "Anytown",
    #         "state": "CA",
    #         "zip": "12345"
    #     },
    # }

    decrypted = data_masker.decrypt(data=encrypted, fields=["email", "address.street"])
    # decrypted = {
    #     "id": 1,
    #     "name": "John Doe",
    #     "age": 30,
    #     "email": "johndoe@example.com",
    #     "address": {
    #         "street": "123 Main St",
    #         "city": "Anytown",
    #         "state": "CA",
    #         "zip": "12345"
    #     },
    # }

    encrypted = data_masker.encrypt(data=data, fields=["email", "address"])
    # encrypted = {
    #     "id": 1,
    #     "name": "John Doe",
    #     "age": 30,
    #     "email": "InRoaXMgaXMgYSBzdHJpbmciHsLZGx2na-XzP_TB5Bf2LNU1bLc",
    #     "address": "XMgYSB_KDddaDJYMb-JpbmGnagTklwQ-msdaDLP"
    # }

    decrypted = data_masker.decrypt(data=encrypted, fields=["email", "address"])
    # decrypted = {
    #     "id": 1,
    #     "name": "John Doe",
    #     "age": 30,
    #     "email": "johndoe@example.com",
    #     "address": {
    #         "street": "123 Main St",
    #         "city": "Anytown",
    #         "state": "CA",
    #         "zip": "12345"
    #     },
    # }

    encrypted = data_masker.encrypt(data=data)
    # encrypted = "InRoaXMgaXMgYSBzdHJpbmciHsLZGx2na-XzP_TB5Bf2LNU1bLc"

    decrypted = data_masker.decrypt(data=encrypted)
    # decrypted = {
    #     "id": 1,
    #     "name": "John Doe",
    #     "age": 30,
    #     "email": "johndoe@example.com",
    #     "address": {
    #         "street": "123 Main St",
    #         "city": "Anytown",
    #         "state": "CA",
    #         "zip": "12345"
    #     },
    # }

    masked = data_masker.mask(data=data, fields=["email", "address.street"])
    # masked = {
    #     "id": 1,
    #     "name": "John Doe",
    #     "age": 30,
    #     "email": "*****",
    #     "address": {
    #         "street": "*****",
    #         "city": "Anytown",
    #         "state": "CA",
    #         "zip": "12345"
    #     },
    # }
