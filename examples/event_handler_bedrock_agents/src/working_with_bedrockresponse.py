from http import HTTPStatus

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.event_handler.api_gateway import BedrockResponse
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = BedrockAgentResolver()


@app.get("/return_with_session", description="Returns a hello world with session attributes")
@tracer.capture_method
def hello_world():
    return BedrockResponse(
        status_code=HTTPStatus.OK.value,
        body={"message": "Hello from Bedrock!"},
        session_attributes={"user_id": "123"},
        prompt_session_attributes={"context": "testing"},
        knowledge_bases_configuration=[
            {
                "knowledgeBaseId": "kb-123",
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {"numberOfResults": 3, "overrideSearchType": "HYBRID"},
                },
            },
        ],
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
