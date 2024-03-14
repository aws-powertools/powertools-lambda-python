from pydantic import EmailStr
from typing_extensions import Annotated

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.event_handler.openapi.params import Body, Query
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = BedrockAgentResolver()  # (1)!


@app.get("/schedule_meeting", description="Schedules a meeting with the team")
@tracer.capture_method
def schedule_meeting(
    email: Annotated[EmailStr, Query(description="The email address of the customer")],  # (2)!
) -> Annotated[bool, Body(description="Whether the meeting was scheduled successfully")]:  # (3)!
    logger.info("Scheduling a meeting", email=email)
    return True


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
