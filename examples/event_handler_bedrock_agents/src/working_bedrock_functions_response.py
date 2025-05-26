from aws_lambda_powertools.event_handler import BedrockAgentFunctionResolver, BedrockFunctionResponse
from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext

app = BedrockAgentFunctionResolver()


@app.tool(description="Function that demonstrates response customization")
def custom_response():
    return BedrockFunctionResponse(
        body="Hello World",
        session_attributes={"user_id": "123"},
        prompt_session_attributes={"last_action": "greeting"},
        response_state="REPROMPT",
        knowledge_bases=[{"name": "kb1", "enabled": True}],
    )


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
