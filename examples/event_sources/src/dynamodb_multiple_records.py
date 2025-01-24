from aws_lambda_powertools.utilities.data_classes import DynamoDBStreamEvent, event_source
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=DynamoDBStreamEvent)
def lambda_handler(event: DynamoDBStreamEvent, context: LambdaContext):
    for record in event.records:
        # {"N": "123.45"} => Decimal("123.45")
        key: str = record.dynamodb.keys["Id"]
    return {"statusCode": 200, "body": f"Key:, {key}!"}
