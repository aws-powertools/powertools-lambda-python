import pytest

from aws_lambda_powertools.utilities.validation import envelopes, exceptions, validate, validator


def test_validate_raw_event(schema, raw_event):
    validate(event=raw_event, schema=schema)


def test_validate_wrapped_event_raw_envelope(schema, wrapped_event):
    validate(event=wrapped_event, schema=schema, envelope="data.payload")


def test_validate_json_string_envelope(schema, wrapped_event_json_string):
    validate(event=wrapped_event_json_string, schema=schema, envelope="powertools_json(data).payload")


def test_validate_base64_string_envelope(schema, wrapped_event_base64_json_string):
    validate(event=wrapped_event_base64_json_string, schema=schema, envelope="powertools_json(powertools_base64(data))")


def test_validate_event_does_not_conform_with_schema(schema):
    with pytest.raises(exceptions.SchemaValidationError):
        validate(event={"message": "hello_world"}, schema=schema)


def test_validate_json_string_no_envelope(schema, wrapped_event_json_string):
    # WHEN data key contains a JSON String
    with pytest.raises(exceptions.SchemaValidationError, match=".*data must be object"):
        validate(event=wrapped_event_json_string, schema=schema, envelope="data.payload")


def test_validate_invalid_schema_format(raw_event):
    with pytest.raises(exceptions.InvalidSchemaFormatError):
        validate(event=raw_event, schema="")


def test_validate_invalid_envelope_expression(schema, wrapped_event):
    with pytest.raises(exceptions.InvalidEnvelopeExpressionError):
        validate(event=wrapped_event, schema=schema, envelope=True)


def test_validate_invalid_event(schema):
    b64_event = "eyJtZXNzYWdlIjogImhlbGxvIGhlbGxvIiwgInVzZXJuYW1lIjogImJsYWggYmxhaCJ9="
    with pytest.raises(exceptions.SchemaValidationError):
        validate(event=b64_event, schema=schema)


def test_apigateway_envelope(schema, apigateway_event):
    # Payload v1 and v2 remains consistent where the payload is (body)
    validate(event=apigateway_event, schema=schema, envelope=envelopes.API_GATEWAY_REST)
    validate(event=apigateway_event, schema=schema, envelope=envelopes.API_GATEWAY_HTTP)


def test_sqs_envelope(sqs_event, schema_array):
    validate(event=sqs_event, schema=schema_array, envelope=envelopes.SQS)


def test_sns_envelope(schema, sns_event):
    validate(event=sns_event, schema=schema, envelope=envelopes.SNS)


def test_eventbridge_envelope(schema, eventbridge_event):
    validate(event=eventbridge_event, schema=schema, envelope=envelopes.EVENTBRIDGE)


def test_kinesis_data_stream_envelope(schema_array, kinesis_event):
    validate(event=kinesis_event, schema=schema_array, envelope=envelopes.KINESIS_DATA_STREAM)


def test_cloudwatch_logs_envelope(cloudwatch_logs_schema, cloudwatch_logs_event):
    validate(event=cloudwatch_logs_event, schema=cloudwatch_logs_schema, envelope=envelopes.CLOUDWATCH_LOGS)


def test_validator_incoming(schema, raw_event):
    @validator(inbound_schema=schema)
    def lambda_handler(evt, context):
        pass

    lambda_handler(raw_event, {})


def test_validator_outgoing(schema_response, raw_response):
    @validator(outbound_schema=schema_response)
    def lambda_handler(evt, context):
        return raw_response

    lambda_handler({}, {})


def test_validator_incoming_and_outgoing(schema, schema_response, raw_event, raw_response):
    @validator(inbound_schema=schema, outbound_schema=schema_response)
    def lambda_handler(evt, context):
        return raw_response

    lambda_handler(raw_event, {})


def test_validator_propagates_exception(schema, raw_event, schema_response):
    @validator(inbound_schema=schema, outbound_schema=schema_response)
    def lambda_handler(evt, context):
        raise ValueError("Bubble up")

    with pytest.raises(ValueError):
        lambda_handler(raw_event, {})
