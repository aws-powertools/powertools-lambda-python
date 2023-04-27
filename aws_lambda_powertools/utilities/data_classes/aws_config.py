from __future__ import annotations

import json
from typing import Dict, List

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


def get_invoke_event(
    invoking_event: dict,
) -> AWSConfigConfigurationChanged | AWSConfigScheduledNotification | AWSConfigOversizedConfiguration | None:
    message_type = invoking_event.get("messageType")

    if message_type == "ConfigurationItemChangeNotification":
        return AWSConfigConfigurationChanged(invoking_event)

    if message_type == "ScheduledNotification":
        return AWSConfigScheduledNotification(invoking_event)

    if message_type == "OversizedConfigurationItemChangeNotification":
        return AWSConfigOversizedConfiguration(invoking_event)

    # In case of a unknown event
    return None


class AWSConfigConfigurationItemChanged(DictWrapper):
    @property
    def related_events(self) -> List:
        """The version of the event."""
        return self["relatedEvents"]

    @property
    def relationships(self) -> List:
        """The version of the event."""
        return self["relationships"]

    @property
    def configuration(self) -> Dict:
        """The version of the event."""
        return self["configuration"]

    @property
    def supplementary_configuration(self) -> Dict:
        """The version of the event."""
        return self["supplementaryConfiguration"]

    @property
    def tags(self) -> Dict:
        """The version of the event."""
        return self["tags"]

    @property
    def configuration_item_version(self) -> str:
        """The version of the event."""
        return self["configurationItemVersion"]

    @property
    def configuration_item_capture_time(self) -> str:
        """The version of the event."""
        return self["configurationItemCaptureTime"]

    @property
    def configuration_state_id(self) -> str:
        """The version of the event."""
        return self["configurationStateId"]

    @property
    def accountid(self) -> str:
        """The version of the event."""
        return self["awsAccountId"]

    @property
    def configuration_item_status(self) -> str:
        """The version of the event."""
        return self["configurationItemStatus"]

    @property
    def resource_type(self) -> str:
        """The version of the event."""
        return self["resourceType"]

    @property
    def resource_id(self) -> str:
        """The version of the event."""
        return self["resourceId"]

    @property
    def resource_name(self) -> str:
        """The version of the event."""
        return self["resourceName"]

    @property
    def resource_arn(self) -> str:
        """The version of the event."""
        return self["ARN"]

    @property
    def region(self) -> str:
        """The version of the event."""
        return self["awsRegion"]

    @property
    def availability_zone(self) -> str:
        """The version of the event."""
        return self["availabilityZone"]

    @property
    def configuration_state_md5_hash(self) -> str:
        """The version of the event."""
        return self["configurationStateMd5Hash"]

    @property
    def resource_creation_time(self) -> str:
        """The version of the event."""
        return self["resourceCreationTime"]


class AWSConfigConfigurationChanged(DictWrapper):
    @property
    def configuration_item_diff(self) -> Dict:
        """The version of the event."""
        return self["configurationItemDiff"]

    @property
    def configuration_item(self) -> AWSConfigConfigurationItemChanged:
        """The version of the event."""
        return AWSConfigConfigurationItemChanged(self["configurationItem"])

    def raw_configuration_item(self) -> Dict:
        """The version of the event."""
        return self["configurationItem"]

    @property
    def record_version(self) -> str:
        """The version of the event."""
        return self["recordVersion"]

    @property
    def message_type(self) -> str:
        """The version of the event."""
        return self["messageType"]

    @property
    def notification_creation_time(self) -> str:
        """The version of the event."""
        return self["notificationCreationTime"]


class AWSConfigScheduledNotification(DictWrapper):
    @property
    def accountid(self) -> str:
        """The version of the event."""
        return self["awsAccountId"]

    @property
    def notification_creation_time(self) -> str:
        """The version of the event."""
        return self["notificationCreationTime"]

    @property
    def record_version(self) -> str:
        """The version of the event."""
        return self["recordVersion"]

    @property
    def message_type(self) -> str:
        """The version of the event."""
        return self["messageType"]


class AWSConfigOversizedConfiguration(DictWrapper):
    @property
    def accountid(self) -> str:
        """The version of the event."""
        return self["awsAccountId"]


class AWSConfigEvent(DictWrapper):
    """Events for AWS Config Rules
    Documentation:
    --------------
    - https://docs.aws.amazon.com/config/latest/developerguide/evaluate-config_develop-rules_lambda-functions.html
    """

    @property
    def version(self) -> str:
        """The version of the event."""
        return self["version"]

    @property
    def invoking_event(
        self,
    ) -> AWSConfigConfigurationChanged | AWSConfigScheduledNotification | AWSConfigOversizedConfiguration | None:
        """The version of the event."""
        return get_invoke_event(json.loads(self["invokingEvent"]))

    @property
    def raw_invoking_event(self) -> str:
        """The version of the event."""
        return self["invokingEvent"]

    @property
    def rule_parameters(self) -> Dict:
        """The parameters of the event."""
        return json.loads(self["ruleParameters"])

    @property
    def result_token(self) -> str:
        """The token of the event."""
        return self["resultToken"]

    @property
    def event_left_scope(self) -> bool:
        """The left scope of the event."""
        return self["eventLeftScope"]

    @property
    def execution_role_arn(self) -> str:
        """The execution role arn of the event."""
        return self["executionRoleArn"]

    @property
    def config_rule_arn(self) -> str:
        """The arn of the rule of the event."""
        return self["configRuleArn"]

    @property
    def config_rule_name(self) -> str:
        """The name of the rule of the event."""
        return self["configRuleArn"]

    @property
    def config_rule_id(self) -> str:
        """The id of the rule of the event."""
        return self["configRuleId"]

    @property
    def accountid(self) -> str:
        """The accountid of the event."""
        return self["accountId"]

    @property
    def evalution_mode(self) -> str:
        """The evalution mode of the event."""
        return self["evaluationMode"]
