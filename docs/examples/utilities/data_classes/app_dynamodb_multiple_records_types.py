from aws_lambda_powertools.utilities.data_classes import DynamoDBStreamEvent, event_source
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import AttributeValue, AttributeValueType
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=DynamoDBStreamEvent)
def lambda_handler(event: DynamoDBStreamEvent, context: LambdaContext):
    for record in event.records:
        key: AttributeValue = record.dynamodb.keys["id"]
        if key == AttributeValueType.Number:
            # {"N": "123.45"} => "123.45"
            assert key.get_value == key.n_value
            print(key.get_value)
        elif key == AttributeValueType.Map:
            assert key.get_value == key.map_value
            print(key.get_value)
