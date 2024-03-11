from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import CloudWatchAlarmEvent, event_source
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@event_source(data_class=CloudWatchAlarmEvent)
def lambda_handler(event: CloudWatchAlarmEvent, context: LambdaContext) -> dict:
    logger.info(f"Alarm {event.alarm_data.alarm_name} state is {event.alarm_data.state.value}")

    # You can now work with event. For example, you can enrich the received data, and
    # decide on how you want to route the alarm.

    return {
        "name": event.alarm_data.alarm_name,
        "arn": event.alarm_arn,
        "urgent": "Priority: P1" in (event.alarm_data.configuration.description or ""),
    }
