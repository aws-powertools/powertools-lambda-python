from aws_lambda_powertools.utilities.batch import sqs_batch_processor


def record_handler(record):
    return do_something_with(record["body"])


@sqs_batch_processor(record_handler=record_handler)
def lambda_handler(event, context):
    return {"statusCode": 200}
