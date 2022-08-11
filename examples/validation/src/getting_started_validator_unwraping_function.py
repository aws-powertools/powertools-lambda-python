import boto3
import getting_started_validator_unwraping_schema as schemas

from aws_lambda_powertools.utilities.validation import validator

s3_client = boto3.resource("s3")


# using a decorator to validate input data
@validator(inbound_schema=schemas.INPUT, envelope="data")
def lambda_handler(event, context):

    try:
        data_detail: dict = event.get("detail", {})
        s3_object = s3_client.Object(data_detail.get("s3_bucket"), data_detail.get("s3_key"))
        content = s3_object.get()["Body"].read().decode("utf-8")

        # return data processed
        return {"message": process_data_object(content), "success": True}

    except s3_client.meta.client.exceptions.NoSuchBucket as exception:
        return return_error_message(str(exception))
    except s3_client.meta.client.exceptions.NoSuchKey as exception:
        return return_error_message(str(exception))


def return_error_message(message: str) -> dict:
    return {"message": message, "success": False}


def process_data_object(content: str) -> str:
    # insert logic here
    return "Data OK"
