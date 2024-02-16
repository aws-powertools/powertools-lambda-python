import datetime
from time import time

from pydantic import BaseModel, EmailStr
from typing_extensions import Annotated

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.event_handler.openapi.params import Body
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = BedrockAgentResolver()  # (1)!


class ScheduleMeetingResponse(BaseModel):  # (2)!
    date: Annotated[datetime.datetime, Body(description="The date of the scheduled meeting")]  # (3)!
    team: Annotated[str, Body(description="The team that will handle the support request")]
    cancellationEmail: Annotated[EmailStr, Body(description="The email address to request a meeting cancellation")]


@app.get("/schedule_meeting", description="Schedules a meeting with the team")
@tracer.capture_method
def schedule_meeting(email: EmailStr) -> ScheduleMeetingResponse:  # (4)!
    logger.info("Scheduling a meeting", email=email)
    return ScheduleMeetingResponse(
        date=datetime.datetime.fromtimestamp(time() + 60 * 60 * 24 * 7),  # 7 days from now
        team="Customer Support Team B",
        cancellationEmail=EmailStr("cancel@example.org"),
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
