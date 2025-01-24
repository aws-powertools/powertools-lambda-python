from typing import List

from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.cloud_watch_logs_event import CloudWatchLogsDecodedData
from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import (
    KinesisStreamEvent,
    extract_cloudwatch_logs_from_event,
)


@event_source(data_class=KinesisStreamEvent)
def lambda_handler(event: KinesisStreamEvent, context):
    logs: List[CloudWatchLogsDecodedData] = extract_cloudwatch_logs_from_event(event)
    for log in logs:
        if log.message_type == "DATA_MESSAGE":
            return "success"
    return "nothing to be processed"
