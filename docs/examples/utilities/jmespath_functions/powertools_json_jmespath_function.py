import schemas

from aws_lambda_powertools.utilities.validation import validate

sample_event = {
    "data": '{"payload": {"message": "hello hello", "username": "blah blah"}}',
}

validate(event=sample_event, schema=schemas.INPUT, envelope="powertools_json(data)")
