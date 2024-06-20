from aws_lambda_powertools.utilities.data_classes import (
    CloudWatchDashboardCustomWidgetEvent,
)
from tests.functional.utils import load_event


def test_cloud_watch_dashboard_event():
    raw_event = load_event("cloudWatchDashboardEvent.json")
    parsed_event = CloudWatchDashboardCustomWidgetEvent(raw_event)

    assert parsed_event.describe is False
    widget_context_raw = raw_event["widgetContext"]
    assert parsed_event.widget_context.account_id == widget_context_raw["accountId"]
    assert parsed_event.widget_context.domain == widget_context_raw["domain"]
    assert parsed_event.widget_context.dashboard_name == widget_context_raw["dashboardName"]
    assert parsed_event.widget_context.widget_id == widget_context_raw["widgetId"]
    assert parsed_event.widget_context.locale == widget_context_raw["locale"]
    assert parsed_event.widget_context.timezone.label == widget_context_raw["timezone"]["label"]
    assert parsed_event.widget_context.timezone.offset_iso == widget_context_raw["timezone"]["offsetISO"]
    assert parsed_event.widget_context.timezone.offset_in_minutes == widget_context_raw["timezone"]["offsetInMinutes"]
    assert parsed_event.widget_context.period == widget_context_raw["period"]
    assert parsed_event.widget_context.is_auto_period is True
    assert parsed_event.widget_context.time_range.mode == widget_context_raw["timeRange"]["mode"]
    assert parsed_event.widget_context.time_range.start == widget_context_raw["timeRange"]["start"]
    assert parsed_event.widget_context.time_range.end == widget_context_raw["timeRange"]["end"]
    assert parsed_event.widget_context.time_range.relative_start == widget_context_raw["timeRange"]["relativeStart"]
    assert parsed_event.widget_context.time_range.zoom_start == widget_context_raw["timeRange"]["zoom"]["start"]
    assert parsed_event.widget_context.time_range.zoom_end == widget_context_raw["timeRange"]["zoom"]["end"]
    assert parsed_event.widget_context.theme == widget_context_raw["theme"]
    assert parsed_event.widget_context.link_charts is True
    assert parsed_event.widget_context.title == widget_context_raw["title"]
    assert parsed_event.widget_context.forms == {}
    assert parsed_event.widget_context.params == {"original": "param-to-widget"}
    assert parsed_event.widget_context.width == widget_context_raw["width"]
    assert parsed_event.widget_context.height == widget_context_raw["height"]
    assert parsed_event.widget_context.params["original"] == "param-to-widget"
    assert parsed_event["original"] == "param-to-widget"
    assert parsed_event.raw_event["original"] == "param-to-widget"


def test_cloud_watch_dashboard_describe_event():
    event = CloudWatchDashboardCustomWidgetEvent({"describe": True})
    assert event.describe is True
    assert event.widget_context is None
    assert event.raw_event == {"describe": True}
