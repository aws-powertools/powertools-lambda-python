from aws_lambda_powertools.utilities.data_classes import (
    CloudWatchDashboardCustomWidgetEvent,
)
from tests.functional.utils import load_event


def test_cloud_watch_dashboard_event():
    event = CloudWatchDashboardCustomWidgetEvent(load_event("cloudWatchDashboardEvent.json"))
    assert event.describe is False
    assert event.widget_context.account_id == "123456789123"
    assert event.widget_context.domain == "https://us-east-1.console.aws.amazon.com"
    assert event.widget_context.dashboard_name == "Name-of-current-dashboard"
    assert event.widget_context.widget_id == "widget-16"
    assert event.widget_context.locale == "en"
    assert event.widget_context.timezone.label == "UTC"
    assert event.widget_context.timezone.offset_iso == "+00:00"
    assert event.widget_context.timezone.offset_in_minutes == 0
    assert event.widget_context.period == 300
    assert event.widget_context.is_auto_period is True
    assert event.widget_context.time_range.mode == "relative"
    assert event.widget_context.time_range.start == 1627236199729
    assert event.widget_context.time_range.end == 1627322599729
    assert event.widget_context.time_range.relative_start == 86400012
    assert event.widget_context.time_range.zoom_start == 1627276030434
    assert event.widget_context.time_range.zoom_end == 1627282956521
    assert event.widget_context.theme == "light"
    assert event.widget_context.link_charts is True
    assert event.widget_context.title == "Tweets for Amazon website problem"
    assert event.widget_context.forms == {}
    assert event.widget_context.params == {"original": "param-to-widget"}
    assert event.widget_context.width == 588
    assert event.widget_context.height == 369
    assert event.widget_context.params["original"] == "param-to-widget"
    assert event["original"] == "param-to-widget"
    assert event.raw_event["original"] == "param-to-widget"


def test_cloud_watch_dashboard_describe_event():
    event = CloudWatchDashboardCustomWidgetEvent({"describe": True})
    assert event.describe is True
    assert event.widget_context is None
    assert event.raw_event == {"describe": True}
