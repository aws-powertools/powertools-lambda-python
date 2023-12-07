from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import BedrockAgentEvent, event_source
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@event_source(data_class=BedrockAgentEvent)
def lambda_handler(event: BedrockAgentEvent, context: LambdaContext) -> dict:
    input_text = event.input_text

    logger.info(f"Bedrock Agent {event.action_group} invoked with input", input_text=input_text)

    return {
        "message_version": "1.0",
        "responses": [
            {
                "action_group": event.action_group,
                "api_path": event.api_path,
                "http_method": event.http_method,
                "http_status_code": 200,
                "response_body": {"application/json": {"body": "This is the response"}},
            },
        ],
    }
