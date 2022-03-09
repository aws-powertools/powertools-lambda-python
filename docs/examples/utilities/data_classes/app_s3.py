from urllib.parse import unquote_plus

from aws_lambda_powertools.utilities.data_classes import S3Event, event_source


@event_source(data_class=S3Event)
def lambda_handler(event: S3Event, context):
    bucket_name = event.bucket_name

    # Multiple records can be delivered in a single event
    for record in event.records:
        object_key = unquote_plus(record.s3.get_object.key)

        do_something_with(f"{bucket_name}/{object_key}")
