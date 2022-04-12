from aws_lambda_powertools.utilities.batch import sqs_batch_processor

...


@sqs_batch_processor(record_handler=record_handler, config=config, suppress_exception=True)
def lambda_handler(event, context):
    return {"statusCode": 200}
