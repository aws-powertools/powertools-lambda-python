import os

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities._data_masking import DataMasking
from aws_lambda_powertools.utilities._data_masking.provider.kms.aws_encryption_sdk import AwsEncryptionSdkProvider
from aws_lambda_powertools.utilities.typing import LambdaContext

KMS_KEY_ARN = os.environ["KMS_KEY_ARN"]

json_blob = {
    "id": 1,
    "name": "John Doe",
    "age": 30,
    "email": "johndoe@example.com",
    "address": {"street": "123 Main St", "city": "Anytown", "state": "CA", "zip": "12345"},
    "phone_numbers": ["+1-555-555-1234", "+1-555-555-5678"],
    "interests": ["Hiking", "Traveling", "Photography", "Reading"],
    "job_history": {
        "company": {
            "company_name": "Acme Inc.",
            "company_address": "5678 Interview Dr.",
        },
        "position": "Software Engineer",
        "start_date": "2015-01-01",
        "end_date": "2017-12-31",
    },
    "about_me": """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla tincidunt velit quis
    sapien mollis, at egestas massa tincidunt. Suspendisse ultrices arcu a dolor dapibus,
    ut pretium turpis volutpat. Vestibulum at sapien quis sapien dignissim volutpat ut a enim.
    Praesent fringilla sem eu dui convallis luctus. Donec ullamcorper, sapien ut convallis congue,
    risus mauris pretium tortor, nec dignissim arcu urna a nisl. Vivamus non fermentum ex. Proin
    interdum nisi id sagittis egestas. Nam sit amet nisi nec quam pharetra sagittis. Aliquam erat
    volutpat. Donec nec luctus sem, nec ornare lorem. Vivamus vitae orci quis enim faucibus placerat.
    Nulla facilisi. Proin in turpis orci. Donec imperdiet velit ac tellus gravida, eget laoreet tellus
    malesuada. Praesent venenatis tellus ac urna blandit, at varius felis posuere. Integer a commodo nunc.
    """,
}

app = APIGatewayRestResolver()
tracer = Tracer()
logger = Logger()


@app.get("/function1024")
@tracer.capture_method
def function1024():
    logger.info("Hello world function1024 - HTTP 200")
    data_masker = DataMasking(provider=AwsEncryptionSdkProvider(keys=[KMS_KEY_ARN]))
    encrypted = data_masker.encrypt(json_blob, fields=["address.street", "job_history.company.company_name"])
    decrypted = data_masker.decrypt(encrypted, fields=["address.street", "job_history.company.company_name"])
    return {"Decrypted_json_blob_function_1024": decrypted}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
