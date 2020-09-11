from aws_lambda_powertools.utilities.validation import validate


def test_validate_raw_event(schema, raw_event):
    validate(event=raw_event, schema=schema)


def test_validate_raw_envelope(schema, wrapped_event):
    validate(event=wrapped_event, schema=schema, envelope="data.payload")


def test_validate_json_string_envelope(schema, wrapped_event_json_string):
    validate(event=wrapped_event_json_string, schema=schema, envelope="powertools_json(data).payload")


def test_validate_base64_string_envelope(schema, wrapped_event_base64_json_string):
    validate(event=wrapped_event_base64_json_string, schema=schema, envelope="powertools_json(powertools_base64(data))")


def test_validate_json_string_no_envelope(schema, wrapped_event_json_string):
    raise NotImplementedError()


def test_invalid_schema_format_exception():
    raise NotImplementedError()


def test_invalid_envelope_expression():
    raise NotImplementedError()


def test_invalid_event():
    raise NotImplementedError()


def test_apigateway_http_envelope():
    raise NotImplementedError()


def test_apigateway_rest_envelope():
    raise NotImplementedError()


def test_eventbridge_envelope():
    raise NotImplementedError()


def test_sqs_envelope():
    raise NotImplementedError()


def test_sns_envelope():
    raise NotImplementedError()


def test_cloudwatch_events_schedule_envelope():
    raise NotImplementedError()


def test_kinesis_data_stream_envelope():
    raise NotImplementedError()


def test_cloudwatch_logs_envelope():
    raise NotImplementedError()


def test_validator_incoming():
    raise NotImplementedError()


def test_validator_outgoing():
    raise NotImplementedError()


def test_validator_incoming_and_outgoing():
    raise NotImplementedError()
