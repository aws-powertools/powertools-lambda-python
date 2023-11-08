from aws_lambda_powertools.utilities.data_masking import DataMasking


def lambda_handler(event, context):

    data_masker = DataMasking()

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

    data_masker.mask(data=data, fields=["email", "address.street", "company_address"])
