import boto3

from aws_lambda_powertools.utilities.batch import sqs_batch_processor

session = boto3.session.Session()


def record_handler(record):
    # This will be called for each individual message from a batch
    # It should raise an exception if the message was not processed successfully
    return_value = do_something_with(record["body"])
    return return_value


@sqs_batch_processor(record_handler=record_handler, boto3_session=session)
def lambda_handler(event, context):
    return {"statusCode": 200}
