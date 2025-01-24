from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import CloudWatchDashboardCustomWidgetEvent, event_source

logger = Logger()


@event_source(data_class=CloudWatchDashboardCustomWidgetEvent)
def lambda_handler(event: CloudWatchDashboardCustomWidgetEvent, context):
    logger.info(f"Processing custom widget for dashboard: {event.widget_context.dashboard_name}")

    # Access specific event properties
    widget_id = event.widget_context.widget_id
    time_range_start = event.widget_context.time_range.start
    time_range_end = event.widget_context.time_range.end

    # Your custom widget logic here
    return {
        "title": f"Custom Widget {widget_id}",
        "markdown": f"""
        Dashboard: {event.widget_context.dashboard_name}
        Time Range: {time_range_start} to {time_range_end}
        Theme: {event.widget_context.theme}
        """,
    }
