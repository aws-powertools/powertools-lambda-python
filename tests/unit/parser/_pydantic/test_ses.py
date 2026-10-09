from aws_lambda_powertools.utilities.parser.models import SesModel, SesRecordModel
from tests.functional.utils import load_event


def test_ses_trigger_event():
    raw_event = load_event("sesEvent.json")
    parsed_event: SesModel = SesModel(**raw_event)

    records = parsed_event.Records
    record: SesRecordModel = records[0]
    raw_record = raw_event["Records"][0]

    assert record.eventSource == raw_record["eventSource"]
    assert record.eventVersion == raw_record["eventVersion"]

    mail = record.ses.mail
    raw_mail = raw_record["ses"]["mail"]
    assert mail.source == raw_mail["source"]
    assert mail.messageId == raw_mail["messageId"]
    assert mail.destination == raw_mail["destination"]
    assert mail.headersTruncated is False
    convert_time = int(round(mail.timestamp.timestamp() * 1000))
    assert convert_time == 0

    headers = list(mail.headers)
    assert len(headers) == 10
    assert headers[0].name == raw_mail["headers"][0]["name"]
    assert headers[0].value == raw_mail["headers"][0]["value"]

    common_headers = mail.commonHeaders
    assert common_headers.returnPath == raw_mail["commonHeaders"]["returnPath"]
    assert common_headers.header_from == raw_mail["commonHeaders"]["from"]
    assert common_headers.date == raw_mail["commonHeaders"]["date"]
    assert common_headers.to == raw_mail["commonHeaders"]["to"]
    assert common_headers.messageId == raw_mail["commonHeaders"]["messageId"]
    assert common_headers.subject == raw_mail["commonHeaders"]["subject"]

    receipt = record.ses.receipt
    raw_receipt = raw_record["ses"]["receipt"]
    convert_time = int(round(receipt.timestamp.timestamp() * 1000))
    assert convert_time == 0
    assert receipt.processingTimeMillis == raw_receipt["processingTimeMillis"]
    assert receipt.recipients == raw_receipt["recipients"]
    assert receipt.spamVerdict.status == raw_receipt["spamVerdict"]["status"]
    assert receipt.virusVerdict.status == raw_receipt["virusVerdict"]["status"]
    assert receipt.spfVerdict.status == raw_receipt["spfVerdict"]["status"]
    assert receipt.dmarcVerdict.status == raw_receipt["dmarcVerdict"]["status"]

    action = receipt.action
    assert action.type == raw_receipt["action"]["type"]
    assert action.functionArn == raw_receipt["action"]["functionArn"]
    assert action.invocationType == raw_receipt["action"]["invocationType"]


def test_ses_reply_to_header():
    from aws_lambda_powertools.utilities.parser.models.ses import SesMailCommonHeaders

    # Test with standard SES notification camelCase payload
    headers_camel = SesMailCommonHeaders.model_validate({
        "from": ["sender@example.com"],
        "to": ["receiver@example.com"],
        "returnPath": "bounce@example.com",
        "messageId": "<msg-001@example.com>",
        "date": "Wed, 7 Oct 2026 12:34:56 -0700",
        "subject": "SES Subject",
        "replyTo": ["reply@example.com"],
    })
    assert headers_camel.reply_to == ["reply@example.com"]
    assert headers_camel.model_dump(by_alias=True)["replyTo"] == ["reply@example.com"]

    # Test backwards compatibility with hyphenated alias
    headers_hyphen = SesMailCommonHeaders.model_validate({
        "from": ["sender@example.com"],
        "to": ["receiver@example.com"],
        "returnPath": "bounce@example.com",
        "messageId": "<msg-002@example.com>",
        "date": "Wed, 7 Oct 2026 12:34:56 -0700",
        "subject": "SES Subject",
        "reply-to": ["reply-hyphen@example.com"],
    })
    assert headers_hyphen.reply_to == ["reply-hyphen@example.com"]

    # Test keyword argument instantiation
    headers_kwarg = SesMailCommonHeaders(
        **{"from": ["sender@example.com"]},
        to=["receiver@example.com"],
        returnPath="bounce@example.com",
        messageId="<msg-003@example.com>",
        date="Wed, 7 Oct 2026 12:34:56 -0700",
        subject="SES Subject",
        reply_to=["reply-kwarg@example.com"],
    )
    assert headers_kwarg.reply_to == ["reply-kwarg@example.com"]

