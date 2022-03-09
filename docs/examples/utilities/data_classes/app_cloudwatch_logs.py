from aws_lambda_powertools.utilities.data_classes import CloudWatchLogsEvent, event_source
from aws_lambda_powertools.utilities.data_classes.cloud_watch_logs_event import CloudWatchLogsDecodedData


@event_source(data_class=CloudWatchLogsEvent)
def lambda_handler(event: CloudWatchLogsEvent, context):
    decompressed_log: CloudWatchLogsDecodedData = event.parse_logs_data
    log_events = decompressed_log.log_events
    for event in log_events:
        do_something_with(event.timestamp, event.message)
