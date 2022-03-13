from botocore.config import Config

from aws_lambda_powertools.utilities.batch import PartialSQSProcessor

config = Config(region_name="us-east-1")


def record_handler(record):
    # This will be called for each individual message from a batch
    # It should raise an exception if the message was not processed successfully
    return_value = do_something_with(record["body"])
    return return_value


def lambda_handler(event, context):
    records = event["Records"]

    processor = PartialSQSProcessor(config=config)

    with processor(records, record_handler):
        result = processor.process()

    return result
