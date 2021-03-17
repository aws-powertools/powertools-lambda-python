from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.parser.models import SesModel, SesRecordModel
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.utils import load_event


@event_parser(model=SesModel)
def handle_ses(event: SesModel, _: LambdaContext):
    expected_address = "johndoe@example.com"
    records = event.Records
    record: SesRecordModel = records[0]
    assert record.eventSource == "aws:ses"
    assert record.eventVersion == "1.0"
    mail = record.ses.mail
    convert_time = int(round(mail.timestamp.timestamp() * 1000))
    assert convert_time == 0
    assert mail.source == "janedoe@example.com"
    assert mail.messageId == "o3vrnil0e2ic28tr"
    assert mail.destination == [expected_address]
    assert mail.headersTruncated is False
    headers = list(mail.headers)
    assert len(headers) == 10
    assert headers[0].name == "Return-Path"
    assert headers[0].value == "<janedoe@example.com>"
    common_headers = mail.commonHeaders
    assert common_headers.returnPath == "janedoe@example.com"
    assert common_headers.header_from == ["Jane Doe <janedoe@example.com>"]
    assert common_headers.date == "Wed, 7 Oct 2015 12:34:56 -0700"
    assert common_headers.to == [expected_address]
    assert common_headers.messageId == "<0123456789example.com>"
    assert common_headers.subject == "Test Subject"
    receipt = record.ses.receipt
    convert_time = int(round(receipt.timestamp.timestamp() * 1000))
    assert convert_time == 0
    assert receipt.processingTimeMillis == 574
    assert receipt.recipients == [expected_address]
    assert receipt.spamVerdict.status == "PASS"
    assert receipt.virusVerdict.status == "PASS"
    assert receipt.spfVerdict.status == "PASS"
    assert receipt.dmarcVerdict.status == "PASS"
    action = receipt.action
    assert action.type == "Lambda"
    assert action.functionArn == "arn:aws:lambda:us-west-2:012345678912:function:Example"
    assert action.invocationType == "Event"


def test_ses_trigger_event():
    event_dict = load_event("sesEvent.json")
    handle_ses(event_dict, LambdaContext())
