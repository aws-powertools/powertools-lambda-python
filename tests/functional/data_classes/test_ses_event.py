from aws_lambda_powertools.utilities.data_classes import SESEvent
from tests.functional.utils import load_event


def test_ses_trigger_event():
    event = SESEvent(load_event("sesEvent.json"))

    expected_address = "johndoe@example.com"
    records = list(event.records)
    record = records[0]
    assert record.event_source == "aws:ses"
    assert record.event_version == "1.0"
    mail = record.ses.mail
    assert mail.timestamp == "1970-01-01T00:00:00.000Z"
    assert mail.source == "janedoe@example.com"
    assert mail.message_id == "o3vrnil0e2ic28tr"
    assert mail.destination == [expected_address]
    assert mail.headers_truncated is False
    headers = list(mail.headers)
    assert len(headers) == 10
    assert headers[0].name == "Return-Path"
    assert headers[0].value == "<janedoe@example.com>"
    common_headers = mail.common_headers
    assert common_headers.return_path == "janedoe@example.com"
    assert common_headers.get_from == common_headers.raw_event["from"]
    assert common_headers.date == "Wed, 7 Oct 2015 12:34:56 -0700"
    assert common_headers.to == [expected_address]
    assert common_headers.message_id == "<0123456789example.com>"
    assert common_headers.subject == "Test Subject"
    assert common_headers.cc is None
    assert common_headers.bcc is None
    assert common_headers.sender is None
    assert common_headers.reply_to is None
    receipt = record.ses.receipt
    assert receipt.timestamp == "1970-01-01T00:00:00.000Z"
    assert receipt.processing_time_millis == 574
    assert receipt.recipients == [expected_address]
    assert receipt.spam_verdict.status == "PASS"
    assert receipt.virus_verdict.status == "PASS"
    assert receipt.spf_verdict.status == "PASS"
    assert receipt.dmarc_verdict.status == "PASS"
    assert receipt.dkim_verdict.status == "PASS"
    assert receipt.dmarc_policy == "reject"
    action = receipt.action
    assert action.get_type == action.raw_event["type"]
    assert action.function_arn == action.raw_event["functionArn"]
    assert action.invocation_type == action.raw_event["invocationType"]
    assert action.topic_arn is None
    assert event.record.raw_event == event["Records"][0]
    assert event.mail.raw_event == event["Records"][0]["ses"]["mail"]
    assert event.receipt.raw_event == event["Records"][0]["ses"]["receipt"]
