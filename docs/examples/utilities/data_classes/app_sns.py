from aws_lambda_powertools.utilities.data_classes import SNSEvent, event_source


@event_source(data_class=SNSEvent)
def lambda_handler(event: SNSEvent, context):
    # Multiple records can be delivered in a single event
    for record in event.records:
        message = record.sns.message
        subject = record.sns.subject

        do_something_with(subject, message)
