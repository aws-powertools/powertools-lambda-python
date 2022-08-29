from typing import Any, Dict, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class TimeZone(DictWrapper):
    @property
    def label(self) -> str:
        """The time range label. Either 'UTC' or 'Local'"""
        return self["label"]

    @property
    def offset_iso(self) -> str:
        """The time range offset in the format +/-00:00"""
        return self["offsetISO"]

    @property
    def offset_in_minutes(self) -> int:
        """The time range offset in minutes"""
        return int(self["offsetInMinutes"])


class TimeRange(DictWrapper):
    @property
    def mode(self) -> str:
        """The time range mode, i.e. 'relative' or 'absolute'"""
        return self["mode"]

    @property
    def start(self) -> int:
        """The start time within the time range"""
        return self["start"]

    @property
    def end(self) -> int:
        """The end time within the time range"""
        return self["end"]

    @property
    def relative_start(self) -> Optional[int]:
        """The relative start time within the time range"""
        return self.get("relativeStart")

    @property
    def zoom_start(self) -> Optional[int]:
        """The start time within the zoomed time range"""
        return (self.get("zoom") or {}).get("start")

    @property
    def zoom_end(self) -> Optional[int]:
        """The end time within the zoomed time range"""
        return (self.get("zoom") or {}).get("end")


class CloudWatchWidgetContext(DictWrapper):
    @property
    def dashboard_name(self) -> str:
        """Get dashboard name, in which the widget is used"""
        return self["dashboardName"]

    @property
    def widget_id(self) -> str:
        """Get widget ID"""
        return self["widgetId"]

    @property
    def domain(self) -> str:
        """AWS domain name"""
        return self["domain"]

    @property
    def account_id(self) -> str:
        """Get AWS Account ID"""
        return self["accountId"]

    @property
    def locale(self) -> str:
        """Get locale language"""
        return self["locale"]

    @property
    def timezone(self) -> TimeZone:
        """Timezone information of the dashboard"""
        return TimeZone(self["timezone"])

    @property
    def period(self) -> int:
        """The period shown on the dashboard"""
        return int(self["period"])

    @property
    def is_auto_period(self) -> bool:
        """Whether auto period is enabled"""
        return bool(self["isAutoPeriod"])

    @property
    def time_range(self) -> TimeRange:
        """The widget time range"""
        return TimeRange(self["timeRange"])

    @property
    def theme(self) -> str:
        """The dashboard theme, i.e. 'light' or 'dark'"""
        return self["theme"]

    @property
    def link_charts(self) -> bool:
        """The widget is linked to other charts"""
        return bool(self["linkCharts"])

    @property
    def title(self) -> str:
        """Get widget title"""
        return self["title"]

    @property
    def params(self) -> Dict[str, Any]:
        """Get widget parameters"""
        return self["params"]

    @property
    def forms(self) -> Dict[str, Any]:
        """Get widget form data"""
        return self["forms"]["all"]

    @property
    def height(self) -> int:
        """Get widget height"""
        return int(self["height"])

    @property
    def width(self) -> int:
        """Get widget width"""
        return int(self["width"])


class CloudWatchDashboardCustomWidgetEvent(DictWrapper):
    """CloudWatch dashboard custom widget event

    You can use a Lambda function to create a custom widget on a CloudWatch dashboard.

    Documentation:
    -------------
    - https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/add_custom_widget_dashboard_about.html
    """

    @property
    def describe(self) -> bool:
        """Display widget documentation"""
        return bool(self.get("describe", False))

    @property
    def widget_context(self) -> Optional[CloudWatchWidgetContext]:
        """The widget context"""
        if self.get("widgetContext"):
            return CloudWatchWidgetContext(self["widgetContext"])

        return None
