from typing import Any, Dict, List, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class EventBridgeEvent(DictWrapper):
    """Amazon EventBridge Event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/eventbridge/latest/userguide/aws-events.html
    """

    @property
    def get_id(self) -> str:
        """A unique value is generated for every event. This can be helpful in tracing events as
        they move through rules to targets, and are processed."""
        # Note: this name conflicts with existing python builtins
        return self["id"]

    @property
    def version(self) -> str:
        """By default, this is set to 0 (zero) in all events."""
        return self["version"]

    @property
    def account(self) -> str:
        """The 12-digit number identifying an AWS account."""
        return self["account"]

    @property
    def time(self) -> str:
        """The event timestamp, which can be specified by the service originating the event.

        If the event spans a time interval, the service might choose to report the start time, so
        this value can be noticeably before the time the event is actually received.
        """
        return self["time"]

    @property
    def region(self) -> str:
        """Identifies the AWS region where the event originated."""
        return self["region"]

    @property
    def resources(self) -> List[str]:
        """This JSON array contains ARNs that identify resources that are involved in the event.
        Inclusion of these ARNs is at the discretion of the service."""
        return self["resources"]

    @property
    def source(self) -> str:
        """Identifies the service that sourced the event. All events sourced from within AWS begin with "aws." """
        return self["source"]

    @property
    def detail_type(self) -> str:
        """Identifies, in combination with the source field, the fields and values that appear in the detail field."""
        return self["detail-type"]

    @property
    def detail(self) -> Dict[str, Any]:
        """A JSON object, whose content is at the discretion of the service originating the event. """
        return self["detail"]

    @property
    def replay_name(self) -> Optional[str]:
        """Identifies whether the event is being replayed and what is the name of the replay."""
        return self["replay-name"]
