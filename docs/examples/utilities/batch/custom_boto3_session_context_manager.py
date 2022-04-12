import boto3

from aws_lambda_powertools.utilities.batch import PartialSQSProcessor

session = boto3.session.Session()


def record_handler(record):
    # This will be called for each individual message from a batch
    # It should raise an exception if the message was not processed successfully
    return_value = do_something_with(record["body"])
    return return_value


def lambda_handler(event, context):
    records = event["Records"]

    processor = PartialSQSProcessor(boto3_session=session)

    with processor(records, record_handler):
        result = processor.process()

    return result
