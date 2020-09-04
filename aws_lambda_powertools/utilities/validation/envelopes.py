"""Built-in envelopes"""

API_GATEWAY_REST = "powertools_json(body)"
API_GATEWAY_HTTP = API_GATEWAY_REST
SQS = "Records[*].body"
SNS = "Records[0].Sns.Message"
EVENTBRIDGE = "detail"
CLOUDWATCH_EVENTS_SCHEDULED = EVENTBRIDGE
KINESIS_DATA_STREAM = "Records[*].kinesis.powertools_base64(data) | powertools_json(@)"
CLOUDWATCH_LOGS = "awslogs.powertools_base64(data) | powertools_json(@)"
