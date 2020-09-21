"""Built-in envelopes"""

API_GATEWAY_REST = "powertools_json(body)"
API_GATEWAY_HTTP = API_GATEWAY_REST
SQS = "Records[*].powertools_json(body)"
SNS = "Records[0].Sns.Message | powertools_json(@)"
EVENTBRIDGE = "detail"
CLOUDWATCH_EVENTS_SCHEDULED = EVENTBRIDGE
KINESIS_DATA_STREAM = "Records[*].kinesis.powertools_json(powertools_base64(data))"
CLOUDWATCH_LOGS = "awslogs.powertools_base64_gzip(data) | powertools_json(@).logEvents[*]"
