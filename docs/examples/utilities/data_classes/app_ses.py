from aws_lambda_powertools.utilities.data_classes import SESEvent, event_source


@event_source(data_class=SESEvent)
def lambda_handler(event: SESEvent, context):
    # Multiple records can be delivered in a single event
    for record in event.records:
        mail = record.ses.mail
        common_headers = mail.common_headers

        do_something_with(common_headers.to, common_headers.subject)
