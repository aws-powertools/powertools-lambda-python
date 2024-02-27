import datetime
from time import time

from pydantic import BaseModel, EmailStr
from typing_extensions import Annotated

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.event_handler.openapi.params import Body, Query
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
def schedule_meeting(
    email: Annotated[EmailStr, Query(description="The email address of the customer")],  # (4)!
) -> Annotated[ScheduleMeetingResponse, Body(description="Scheduled meeting details")]:
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


if __name__ == "__main__":
    from dataclasses import dataclass

    @dataclass
    class FakeLambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        aws_request_id: str = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

    print(
        lambda_handler(
            {
                "sessionId": "123456789012345",
                "sessionAttributes": {},
                "inputText": "Schedule a meeting with the team. My email is foo@example.org",
                "promptSessionAttributes": {},
                "apiPath": "/schedule_meeting",
                "parameters": [
                    {
                        "name": "email",
                        "type": "string",
                        "value": "rubefons@amazon.com",
                    },
                ],
                "agent": {
                    "name": "TimeAgent",
                    "version": "DRAFT",
                    "id": "XLHH72XNF2",
                    "alias": "TSTALIASID",
                },
                "httpMethod": "GET",
                "messageVersion": "1.0",
                "actionGroup": "SupportAssistant",
            },
            FakeLambdaContext(),
        ),
    )
