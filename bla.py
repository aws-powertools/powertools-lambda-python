# KMS_KEYS = ["arn:aws:kms:eu-west-1:231436140809:key/1053c7d7-97d7-49ca-9763-5214f28999cc"]

# from aws_lambda_powertools.utilities.data_masking import DataMasking
# from aws_lambda_powertools.utilities.data_masking.provider.kms.aws_encryption_sdk import (
#     AWSEncryptionSDKProvider,
# )


# # from aws_lambda_powertools import Logger

# # from aws_lambda_powertools.logging.utils import copy_config_to_registered_loggers

# # logger = Logger()

# # copy_config_to_registered_loggers(source_logger=logger, log_level="DEBUG")

# # def test_encryption_context_kms_api(data: bytes):
# #     import boto3

# #     kms = boto3.client("kms")
# #     cipher = kms.encrypt(KeyId=KMS_KEYS[0], Plaintext=data, EncryptionContext={"h": "e"})

# #     # When encryption context isn't an exact match
# #     # botocore.errorfactory.InvalidCiphertextException: An error occurred (InvalidCiphertextException) when calling the Decrypt operation:
# #     kms.decrypt(CiphertextBlob=cipher["CiphertextBlob"])


# encryption_provider = AWSEncryptionSDKProvider(keys=KMS_KEYS)
# masker = DataMasking(provider=encryption_provider)


# data = {
#     "name": "Leandro",
#     "operation": "non sensitive",
#     "card_number": "1000 4444 333 2222",
#     "address": [
#         {
#             "postcode": 81847,
#             "street": "38986 Joanne Stravenue",
#             "country": "United States",
#             "timezone": "America/La_Paz",
#         },
#         {"postcode": 94400, "street": "623 Kraig Mall", "country": "United States", "timezone": "America/Mazatlan"},
#     ],
# }


# fields = ["address[*].postcode"]
# encrypted = masker.encrypt(data, fields, data_classification="10", data_type="customer_data")
# output = f"""
# ========================Encrypted blob========================

# {masker.encrypt(data)}

# ========================Field encrypted=======================

# {encrypted}

# ========================Decrypted=============================


# {masker.decrypt(encrypted, data_type="customer_data", data_classification="10")}

# ==============================================================
# """

# print(output)

# # encrypted_data = {
# #     "zip": [
# #         {
# #             "postcode": "AgV4cx2NbEYAiNulToXGoaFxGB8avUnn0C5yuECrPbTgrmkAXwABABVhd3MtY3J5cHRvLXB1YmxpYy1rZXkAREFtV0hyRzROQ0h3Z1hSQmFGVDZCemUwT2dzMGVsK2tTL2hUV1FKZnZrTjJ3OUNQYlk2bTg3QmF0MVJ3NmdNUWNIZz09AAEAB2F3cy1rbXMAS2Fybjphd3M6a21zOmV1LXdlc3QtMToyMzE0MzYxNDA4MDk6a2V5LzEwNTNjN2Q3LTk3ZDctNDljYS05NzYzLTUyMTRmMjg5OTljYwC4AQIBAHgWR9amI/KXfzepTHbCvEUXLMN8D5Fzkp9W3nvbLFphtgF1vgCkRBJno+apgeramUnFAAAAfjB8BgkqhkiG9w0BBwagbzBtAgEAMGgGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQM1s93BzUOeCTYIFJ/AgEQgDvhPDdfMN6dPAdQN16djAUhoYjkdIbKx+g9VBp2HZ8RF2gBvsla3chPkTR+ElfanPiEqt49rL2c46RvVwIAABAAV8XWwONI8SlcSYaGblM516qB6gh93eEb2DlWbt8uo13BpgdjZhYEIzRU7C+Nmoq6/////wAAAAEAAAAAAAAAAAAAAAEAAAAHfIP2Crb6uIIkj0KnT2y34JUyKL/L3TAAZzBlAjAqPfOXUJBmB3BpUL4VT4xaHVSv74wfrqtHbTVKrzvTKpb7AdwMJTEXLHXcZwQXncwCMQCX82+7r6wZ7aE1d7c/thDLB/w3HcFAvEadnBsBbkGrMpSZrI6TiRuqSE4EIZZLNWc="
# #         }
# #     ],
# #     "name": "Lessa",
# #     "operation": "non sensitive",
# #     "card_number": "1000 4444 333 2222",
# # }
