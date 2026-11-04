import base64
import json
import zlib

from aws_lambda_powertools.utilities.parser import envelopes, parse


def _make_cloudwatch_event(log_events: list[dict]) -> dict:
    inner = {
        "messageType": "DATA_MESSAGE",
        "owner": "123456789012",
        "logGroup": "/aws/lambda/my-function",
        "logStream": "2024/10/21/[$LATEST]abcdef1234567890",
        "subscriptionFilters": ["my-filter"],
        "logEvents": log_events,
    }
    compressed = zlib.compress(json.dumps(inner).encode("utf-8"), -1)
    return {"awslogs": {"data": base64.b64encode(compressed)}}


def test_cloudwatch_envelope_handles_non_json_messages():
    plain_text_messages = [
        "START RequestId: eadc91c8-8273-4a2d-b170-b0a7883b619e Version: $LATEST\n",
        "2024-10-21T14:28:15.158Z\teadc91c8-8273-4a2d-b170-b0a7883b619e\tINFO\tHello from handler\n",
        "END RequestId: eadc91c8-8273-4a2d-b170-b0a7883b619e\n",
        "REPORT RequestId: eadc91c8-8273-4a2d-b170-b0a7883b619e\tDuration: 2.07 ms\tBilled Duration: 3 ms\t"
        "Memory Size: 128 MB\tMax Memory Used: 67 MB\t\n",
    ]

    log_events = [
        {"id": f"event-{i}", "timestamp": 1729520895158 + i, "message": msg}
        for i, msg in enumerate(plain_text_messages)
    ]

    raw_event = _make_cloudwatch_event(log_events)

    parsed = parse(
        event=raw_event,
        model=str,
        envelope=envelopes.CloudWatchLogsEnvelope,
    )

    assert len(parsed) == len(plain_text_messages)
    for i, msg in enumerate(plain_text_messages):
        assert parsed[i] == msg


def test_cloudwatch_envelope_handles_mixed_json_and_plain_text():
    json_message = {"level": "INFO", "message": "hello"}
    messages = [
        "START RequestId: eadc91c8-8273-4a2d-b170-b0a7883b619e Version: $LATEST\n",
        json.dumps(json_message),
        "END RequestId: eadc91c8-8273-4a2d-b170-b0a7883b619e\n",
    ]

    log_events = [{"id": f"event-{i}", "timestamp": 1729520895158 + i, "message": msg} for i, msg in enumerate(messages)]

    parsed = parse(
        event=_make_cloudwatch_event(log_events),
        model=str,
        envelope=envelopes.CloudWatchLogsEnvelope,
    )

    assert parsed[0] == messages[0]
    assert parsed[1] == json.dumps(json_message)
    assert parsed[2] == messages[2]
