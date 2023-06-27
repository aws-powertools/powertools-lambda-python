from aws_lambda_powertools.utilities.data_classes import SESEvent
from tests.functional.utils import load_event


def test_ses_trigger_event():
    raw_event = load_event("sesEvent.json")
    parsed_event = SESEvent(raw_event)

    expected_address = "johndoe@example.com"
    records = list(parsed_event.records)
    record = records[0]
    assert record.event_source == raw_event["Records"][0]["eventSource"]
    assert record.event_version == raw_event["Records"][0]["eventVersion"]
    mail = record.ses.mail
    assert mail.timestamp == raw_event["Records"][0]["ses"]["mail"]["timestamp"]
    assert mail.source == raw_event["Records"][0]["ses"]["mail"]["source"]
    assert mail.message_id == raw_event["Records"][0]["ses"]["mail"]["messageId"]
    assert mail.destination == [expected_address]
    assert mail.headers_truncated is False
    headers = list(mail.headers)
    assert len(headers) == 10
    assert headers[0].name == raw_event["Records"][0]["ses"]["mail"]["headers"][0]["name"]
    assert headers[0].value == raw_event["Records"][0]["ses"]["mail"]["headers"][0]["value"]
    common_headers = mail.common_headers
    common_headers_raw = raw_event["Records"][0]["ses"]["mail"]["commonHeaders"]
    assert common_headers.return_path == common_headers_raw["returnPath"]
    assert common_headers.get_from == common_headers.raw_event["from"]
    assert common_headers.date == common_headers_raw["date"]
    assert common_headers.to == [expected_address]
    assert common_headers.message_id == common_headers_raw["messageId"]
    assert common_headers.subject == common_headers_raw["subject"]
    assert common_headers.cc is None
    assert common_headers.bcc is None
    assert common_headers.sender is None
    assert common_headers.reply_to is None
    receipt = record.ses.receipt
    raw_receipt = raw_event["Records"][0]["ses"]["receipt"]
    assert receipt.timestamp == raw_receipt["timestamp"]
    assert receipt.processing_time_millis == raw_receipt["processingTimeMillis"]
    assert receipt.recipients == [expected_address]
    assert receipt.spam_verdict.status == raw_receipt["spamVerdict"]["status"]
    assert receipt.virus_verdict.status == raw_receipt["virusVerdict"]["status"]
    assert receipt.spf_verdict.status == raw_receipt["spfVerdict"]["status"]
    assert receipt.dmarc_verdict.status == raw_receipt["dmarcVerdict"]["status"]
    assert receipt.dkim_verdict.status == raw_receipt["dkimVerdict"]["status"]
    assert receipt.dmarc_policy == raw_receipt["dmarcPolicy"]
    action = receipt.action
    raw_action = raw_event["Records"][0]["ses"]["receipt"]["action"]
    assert action.get_type == raw_action["type"]
    assert action.function_arn == raw_action["functionArn"]
    assert action.invocation_type == raw_action["invocationType"]
    assert action.topic_arn is None
    assert parsed_event.record.raw_event == raw_event["Records"][0]
    assert parsed_event.mail.raw_event == raw_event["Records"][0]["ses"]["mail"]
    assert parsed_event.receipt.raw_event == raw_event["Records"][0]["ses"]["receipt"]
