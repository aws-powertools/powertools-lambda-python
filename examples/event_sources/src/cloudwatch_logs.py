from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import CloudWatchLogsEvent, event_source
from aws_lambda_powertools.utilities.data_classes.cloud_watch_logs_event import CloudWatchLogsDecodedData

logger = Logger()


@event_source(data_class=CloudWatchLogsEvent)
def lambda_handler(event: CloudWatchLogsEvent, context):
    decompressed_log: CloudWatchLogsDecodedData = event.parse_logs_data()

    logger.info(f"Log group: {decompressed_log.log_group}")
    logger.info(f"Log stream: {decompressed_log.log_stream}")

    for log_event in decompressed_log.log_events:
        logger.info(f"Timestamp: {log_event.timestamp}, Message: {log_event.message}")

    return {"statusCode": 200, "body": f"Processed {len(decompressed_log.log_events)} log events"}
