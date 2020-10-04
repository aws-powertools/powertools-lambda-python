from .dynamodb import DynamoDBEnvelope
from .event_bridge import EventBridgeEnvelope
from .sqs import SqsEnvelope

SQS = SqsEnvelope
DYNAMODB_STREAM = DynamoDBEnvelope
EVENTBRIDGE = EventBridgeEnvelope
