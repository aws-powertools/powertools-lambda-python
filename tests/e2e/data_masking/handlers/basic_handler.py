from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from aws_lambda_powertools.utilities.data_masking.providers.aws_encryption_sdk import AwsEncryptionSdkProvider

logger = Logger()


@logger.inject_lambda_context
def lambda_handler(event, context):
    # Generating logs for test_encryption_in_logs test
    message, append_keys = event.get("message", ""), event.get("append_keys", {})
    logger.append_keys(**append_keys)
    logger.info(message)

    kms_key = event.get("kms_key")
    data_masker = DataMasking(provider=AwsEncryptionSdkProvider(keys=[kms_key]))
    value = [1, 2, "string", 4.5]
    encrypted_data = data_masker.encrypt(value)
    response = {}
    response["encrypted_data"] = encrypted_data

    return response
