import os

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities._data_masking import DataMasking
from aws_lambda_powertools.utilities._data_masking.provider.kms.aws_encryption_sdk import AwsEncryptionSdkProvider
from aws_lambda_powertools.utilities.typing import LambdaContext

KMS_KEY_ARN = os.getenv("KMS_KEY_ARN")

tracer = Tracer()
logger = Logger()


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info("Hello world function - HTTP 200")

    data = event["body"]

    data_masker = DataMasking(provider=AwsEncryptionSdkProvider(keys=[KMS_KEY_ARN]))
    encrypted = data_masker.encrypt(data, fields=["address.street", "job_history.company.company_name"])
    decrypted = data_masker.decrypt(encrypted, fields=["address.street", "job_history.company.company_name"])
    return {"Decrypted_json": decrypted}
