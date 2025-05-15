from aws_lambda_powertools.event_handler import BedrockAgentFunctionResolver, BedrockFunctionResponse

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
