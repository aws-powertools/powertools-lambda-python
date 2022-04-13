import schema

from aws_lambda_powertools.utilities.validation import validate

custom_format = {
    "int64": True,  # simply ignore it,
    "positive": lambda x: False if x < 0 else True,
}

validate(event=event, schema=schemas.INPUT, formats=custom_format)
