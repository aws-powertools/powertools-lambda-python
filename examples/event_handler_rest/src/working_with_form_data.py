from typing import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import Form

app = APIGatewayRestResolver(enable_validation=True)


@app.post("/submit_form")
def upload_file(
    name: Annotated[str, Form(description="Your name")],
    age: Annotated[str, Form(description="Your age")],
):
    # You can access form data
    return {"message": f"Your name is {name} and age is {age}"}


def lambda_handler(event, context):
    return app.resolve(event, context)
