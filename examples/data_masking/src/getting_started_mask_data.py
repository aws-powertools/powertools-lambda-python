from aws_lambda_powertools.utilities._data_masking import DataMasking


def lambda_handler(event, context):

    data_masker = DataMasking()

    data = event["body"]

    data_masker.mask(data=data, fields=["email", "address.street", "company_address"])
