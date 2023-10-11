from aws_lambda_powertools.utilities.data_masking import DataMasking


def lambda_handler(event, context: LambdaContext):

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
    }

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

    masked = data_masker.mask(data=data, fields=["address"])
    # masked = {
    #     "id": 1,
    #     "name": "John Doe",
    #     "age": 30,
    #     "email": "johndoe@example.com",
    #     "address": "*****"
    # }

    masked = data_masker.mask(data=data)
    # masked = "*****"
