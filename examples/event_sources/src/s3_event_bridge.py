from aws_lambda_powertools.utilities.data_classes import S3EventBridgeNotificationEvent, event_source


@event_source(data_class=S3EventBridgeNotificationEvent)
def lambda_handler(event: S3EventBridgeNotificationEvent, context):
    bucket_name = event.detail.bucket.name
    file_key = event.detail.object.key
    if event.detail_type == "Object Created":
        print(f"Object {file_key} created in bucket {bucket_name}")
    return {
        "bucket": bucket_name,
        "file_key": file_key,
    }
