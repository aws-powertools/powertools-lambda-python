from aws_lambda_powertools.utilities.data_classes import DynamoDBStreamEvent, event_source
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=DynamoDBStreamEvent)
def lambda_handler(event: DynamoDBStreamEvent, context: LambdaContext):
    processed_keys = []
    for record in event.records:
        if record.dynamodb and record.dynamodb.keys and "Id" in record.dynamodb.keys:
            key = record.dynamodb.keys["Id"]
            processed_keys.append(key)

    return {"statusCode": 200, "body": f"Processed keys: {processed_keys}"}
