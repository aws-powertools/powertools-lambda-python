from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import CloudWatchDashboardCustomWidgetEvent, event_source

logger = Logger()


@event_source(data_class=CloudWatchDashboardCustomWidgetEvent)
def lambda_handler(event: CloudWatchDashboardCustomWidgetEvent, context):
    if event.widget_context is None:
        logger.warning("No widget context provided")
        return {"title": "Error", "markdown": "Widget context is missing"}

    logger.info(f"Processing custom widget for dashboard: {event.widget_context.dashboard_name}")

    # Access specific event properties
    widget_id = event.widget_context.widget_id
    time_range = event.widget_context.time_range

    if time_range is None:
        logger.warning("No time range provided")
        return {"title": f"Custom Widget {widget_id}", "markdown": "Time range is missing"}

    # Your custom widget logic here
    return {
        "title": f"Custom Widget {widget_id}",
        "markdown": f"""
        Dashboard: {event.widget_context.dashboard_name}
        Time Range: {time_range.start} to {time_range.end}
        Theme: {event.widget_context.theme or 'default'}
        """,
    }
