from __future__ import annotations

from typing import Any, Dict, List, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


def get_invoke_event(
    invoking_event: dict,
) -> AWSConfigConfigurationChanged | AWSConfigScheduledNotification | AWSConfigOversizedConfiguration:
    """
    Returns the corresponding event object based on the messageType in the invoking event.

    Parameters
    ----------
    invoking_event: dict
        The invoking event received.

    Returns
    -------
    AWSConfigConfigurationChanged | AWSConfigScheduledNotification | AWSConfigOversizedConfiguration:
        The event object based on the messageType in the invoking event.
    """

    message_type = invoking_event.get("messageType")

    if message_type == "ScheduledNotification":
        return AWSConfigScheduledNotification(invoking_event)

    if message_type == "OversizedConfigurationItemChangeNotification":
        return AWSConfigOversizedConfiguration(invoking_event)

    # Default return is AWSConfigConfigurationChanged event
    return AWSConfigConfigurationChanged(invoking_event)


class AWSConfigConfigurationChanged(DictWrapper):
    @property
    def configuration_item_diff(self) -> Dict:
        """The configuration item diff of the ConfigurationItemChangeNotification event."""
        return self["configurationItemDiff"]

    @property
    def configuration_item(self) -> AWSConfigConfigurationItemChanged:
        """The configuration item of the ConfigurationItemChangeNotification event."""
        return AWSConfigConfigurationItemChanged(self["configurationItem"])

    @property
    def raw_configuration_item(self) -> Dict:
        """The raw configuration item of the ConfigurationItemChangeNotification event."""
        return self["configurationItem"]

    @property
    def record_version(self) -> str:
        """The record version of the ConfigurationItemChangeNotification event."""
        return self["recordVersion"]

    @property
    def message_type(self) -> str:
        """The message type of the ConfigurationItemChangeNotification event."""
        return self["messageType"]

    @property
    def notification_creation_time(self) -> str:
        """The notification creation time of the ConfigurationItemChangeNotification event."""
        return self["notificationCreationTime"]


class AWSConfigConfigurationItemChanged(DictWrapper):
    @property
    def related_events(self) -> List:
        """The related events of the ConfigurationItemChangeNotification event."""
        return self["relatedEvents"]

    @property
    def relationships(self) -> List:
        """The relationships of the ConfigurationItemChangeNotification event."""
        return self["relationships"]

    @property
    def configuration(self) -> Dict:
        """The configuration of the ConfigurationItemChangeNotification event."""
        return self["configuration"]

    @property
    def supplementary_configuration(self) -> Dict:
        """The supplementary configuration of the ConfigurationItemChangeNotification event."""
        return self["supplementaryConfiguration"]

    @property
    def tags(self) -> Dict:
        """The tags of the ConfigurationItemChangeNotification event."""
        return self["tags"]

    @property
    def configuration_item_version(self) -> str:
        """The configuration item version of the ConfigurationItemChangeNotification event."""
        return self["configurationItemVersion"]

    @property
    def configuration_item_capture_time(self) -> str:
        """The configuration item capture time of the ConfigurationItemChangeNotification event."""
        return self["configurationItemCaptureTime"]

    @property
    def configuration_state_id(self) -> str:
        """The configuration state id of the ConfigurationItemChangeNotification event."""
        return self["configurationStateId"]

    @property
    def accountid(self) -> str:
        """The accountid of the ConfigurationItemChangeNotification event."""
        return self["awsAccountId"]

    @property
    def configuration_item_status(self) -> str:
        """The configuration item status of the ConfigurationItemChangeNotification event."""
        return self["configurationItemStatus"]

    @property
    def resource_type(self) -> str:
        """The resource type of the ConfigurationItemChangeNotification event."""
        return self["resourceType"]

    @property
    def resource_id(self) -> str:
        """The resource id of the ConfigurationItemChangeNotification event."""
        return self["resourceId"]

    @property
    def resource_name(self) -> str:
        """The resource name of the ConfigurationItemChangeNotification event."""
        return self["resourceName"]

    @property
    def resource_arn(self) -> str:
        """The resource arn of the ConfigurationItemChangeNotification event."""
        return self["ARN"]

    @property
    def region(self) -> str:
        """The region of the ConfigurationItemChangeNotification event."""
        return self["awsRegion"]

    @property
    def availability_zone(self) -> str:
        """The availability zone of the ConfigurationItemChangeNotification event."""
        return self["availabilityZone"]

    @property
    def configuration_state_md5_hash(self) -> str:
        """The md5 hash of the state of the ConfigurationItemChangeNotification event."""
        return self["configurationStateMd5Hash"]

    @property
    def resource_creation_time(self) -> str:
        """The resource creation time of the ConfigurationItemChangeNotification event."""
        return self["resourceCreationTime"]


class AWSConfigScheduledNotification(DictWrapper):
    @property
    def accountid(self) -> str:
        """The accountid of the ScheduledNotification event."""
        return self["awsAccountId"]

    @property
    def notification_creation_time(self) -> str:
        """The notification creation time of the ScheduledNotification event."""
        return self["notificationCreationTime"]

    @property
    def record_version(self) -> str:
        """The record version of the ScheduledNotification event."""
        return self["recordVersion"]

    @property
    def message_type(self) -> str:
        """The message type of the ScheduledNotification event."""
        return self["messageType"]


class AWSConfigOversizedConfiguration(DictWrapper):
    @property
    def configuration_item_summary(self) -> AWSConfigOversizedConfigurationItemSummary:
        """The configuration item summary of the OversizedConfiguration event."""
        return AWSConfigOversizedConfigurationItemSummary(self["configurationItemSummary"])

    @property
    def raw_configuration_item_summary(self) -> str:
        """The raw configuration item summary of the OversizedConfiguration event."""
        return self["configurationItemSummary"]

    @property
    def message_type(self) -> str:
        """The message type of the OversizedConfiguration event."""
        return self["messageType"]

    @property
    def notification_creation_time(self) -> str:
        """The notification creation time of the OversizedConfiguration event."""
        return self["notificationCreationTime"]

    @property
    def record_version(self) -> str:
        """The record version of the OversizedConfiguration event."""
        return self["recordVersion"]


class AWSConfigOversizedConfigurationItemSummary(DictWrapper):
    @property
    def change_type(self) -> str:
        """The change type of the OversizedConfiguration event."""
        return self["changeType"]

    @property
    def configuration_item_version(self) -> str:
        """The configuration item version of the OversizedConfiguration event."""
        return self["configurationItemVersion"]

    @property
    def configuration_item_capture_time(self) -> str:
        """The configuration item capture time of the OversizedConfiguration event."""
        return self["configurationItemCaptureTime"]

    @property
    def configuration_state_id(self) -> str:
        """The configuration state id of the OversizedConfiguration event."""
        return self["configurationStateId"]

    @property
    def accountid(self) -> str:
        """The accountid of the OversizedConfiguration event."""
        return self["awsAccountId"]

    @property
    def configuration_item_status(self) -> str:
        """The configuration item status of the OversizedConfiguration event."""
        return self["configurationItemStatus"]

    @property
    def resource_type(self) -> str:
        """The resource type of the OversizedConfiguration event."""
        return self["resourceType"]

    @property
    def resource_id(self) -> str:
        """The resource id of the OversizedConfiguration event."""
        return self["resourceId"]

    @property
    def resource_name(self) -> str:
        """The resource name of the OversizedConfiguration event."""
        return self["resourceName"]

    @property
    def resource_arn(self) -> str:
        """The resource arn of the OversizedConfiguration event."""
        return self["ARN"]

    @property
    def region(self) -> str:
        """The region of the OversizedConfiguration event."""
        return self["awsRegion"]

    @property
    def availability_zone(self) -> str:
        """The availability zone of the OversizedConfiguration event."""
        return self["availabilityZone"]

    @property
    def configuration_state_md5_hash(self) -> str:
        """The state md5 hash  of the OversizedConfiguration event."""
        return self["configurationStateMd5Hash"]

    @property
    def resource_creation_time(self) -> str:
        """The resource creation time of the OversizedConfiguration event."""
        return self["resourceCreationTime"]


class AWSConfigRuleEvent(DictWrapper):
    """Events for AWS Config Rules
    Documentation:
    --------------
    - https://docs.aws.amazon.com/config/latest/developerguide/evaluate-config_develop-rules_lambda-functions.html
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self._invoking_event: Optional[Any] = None
        self._rule_parameters: Optional[Any] = None

    @property
    def version(self) -> str:
        """The version of the event."""
        return self["version"]

    @property
    def invoking_event(
        self,
    ) -> AWSConfigConfigurationChanged | AWSConfigScheduledNotification | AWSConfigOversizedConfiguration:
        """The invoking payload of the event."""
        if self._invoking_event is None:
            self._invoking_event = self._json_deserializer(self["invokingEvent"])

        return get_invoke_event(self._invoking_event)

    @property
    def raw_invoking_event(self) -> str:
        """The raw invoking payload of the event."""
        return self["invokingEvent"]

    @property
    def rule_parameters(self) -> Dict:
        """The parameters of the event."""
        if self._rule_parameters is None:
            self._rule_parameters = self._json_deserializer(self["ruleParameters"])

        return self._rule_parameters

    @property
    def result_token(self) -> str:
        """The result token of the event."""
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
        return self["configRuleName"]

    @property
    def config_rule_id(self) -> str:
        """The id of the rule of the event."""
        return self["configRuleId"]

    @property
    def accountid(self) -> str:
        """The accountid of the event."""
        return self["accountId"]

    @property
    def evalution_mode(self) -> Optional[str]:
        """The evalution mode of the event."""
        return self.get("evaluationMode")
