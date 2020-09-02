"""Built-in envelopes"""

API_GATEWAY_REST = "powertools(body)"
API_GATEWAY_HTTP = API_GATEWAY_REST
SQS = "Records[*].body"
SNS = "Records[0].Sns.Message"
EVENTBRIDGE = "detail"
CLOUDWATCH_EVENTS_SCHEDULED = EVENTBRIDGE
