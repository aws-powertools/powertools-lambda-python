import schemas

from aws_lambda_powertools.utilities.validation import validate

sample_event = {
    "data": "eyJtZXNzYWdlIjogImhlbGxvIGhlbGxvIiwgInVzZXJuYW1lIjogImJsYWggYmxhaCJ9=",
}

validate(
    event=sample_event,
    schema=schemas.INPUT,
    envelope="powertools_json(powertools_base64(data))",
)
