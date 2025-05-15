from pydantic import EmailStr

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import BedrockAgentFunctionResolver
from aws_lambda_powertools.event_handler.bedrock_agent_function import BedrockFunctionResponse

tracer = Tracer()
logger = Logger()
app = BedrockAgentFunctionResolver()


@app.tool(description="Schedules a meeting with the team")
@tracer.capture_method
def schedule_meeting(email: EmailStr) -> BedrockFunctionResponse:
    logger.info("Scheduling a meeting", email=email)
    return BedrockFunctionResponse(body=True, session_attributes={"last_email": str(email)})


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context):
    return app.resolve(event, context)
