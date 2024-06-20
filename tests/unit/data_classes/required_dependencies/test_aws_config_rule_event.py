import json

from aws_lambda_powertools.utilities.data_classes import AWSConfigRuleEvent
from tests.functional.utils import load_event


def test_aws_config_rule_configuration_changed():
    """Check AWS Config ConfigurationItemChangeNotification event"""

    raw_event = load_event("awsConfigRuleConfigurationChanged.json")
    parsed_event = AWSConfigRuleEvent(raw_event)

    invoking_event = json.loads(raw_event["invokingEvent"])

    assert parsed_event.rule_parameters == json.loads(raw_event["ruleParameters"])
    assert parsed_event.raw_invoking_event == raw_event["invokingEvent"]
    assert parsed_event.result_token == raw_event["resultToken"]
    assert parsed_event.event_left_scope == raw_event["eventLeftScope"]
    assert parsed_event.execution_role_arn == raw_event["executionRoleArn"]
    assert parsed_event.config_rule_arn == raw_event["configRuleArn"]
    assert parsed_event.config_rule_name == raw_event["configRuleName"]
    assert parsed_event.config_rule_id == raw_event["configRuleId"]
    assert parsed_event.accountid == raw_event["accountId"]
    assert parsed_event.version == raw_event["version"]
    assert parsed_event.evalution_mode == raw_event["evaluationMode"]
    assert parsed_event.invoking_event.message_type == invoking_event["messageType"]
    assert parsed_event.invoking_event.raw_configuration_item == invoking_event["configurationItem"]
    assert parsed_event.invoking_event.record_version == invoking_event["recordVersion"]
    assert parsed_event.invoking_event.notification_creation_time == invoking_event["notificationCreationTime"]
    assert parsed_event.invoking_event.configuration_item_diff == invoking_event["configurationItemDiff"]
    assert (
        parsed_event.invoking_event.configuration_item.related_events
        == invoking_event["configurationItem"]["relatedEvents"]
    )
    assert (
        parsed_event.invoking_event.configuration_item.relationships
        == invoking_event["configurationItem"]["relationships"]
    )
    assert (
        parsed_event.invoking_event.configuration_item.configuration
        == invoking_event["configurationItem"]["configuration"]
    )
    assert (
        parsed_event.invoking_event.configuration_item.supplementary_configuration
        == invoking_event["configurationItem"]["supplementaryConfiguration"]
    )
    assert parsed_event.invoking_event.configuration_item.tags == invoking_event["configurationItem"]["tags"]
    assert (
        parsed_event.invoking_event.configuration_item.configuration_item_version
        == invoking_event["configurationItem"]["configurationItemVersion"]
    )
    assert (
        parsed_event.invoking_event.configuration_item.configuration_item_capture_time
        == invoking_event["configurationItem"]["configurationItemCaptureTime"]
    )
    assert (
        parsed_event.invoking_event.configuration_item.configuration_state_id
        == invoking_event["configurationItem"]["configurationStateId"]
    )
    assert (
        parsed_event.invoking_event.configuration_item.accountid == invoking_event["configurationItem"]["awsAccountId"]
    )
    assert (
        parsed_event.invoking_event.configuration_item.configuration_item_status
        == invoking_event["configurationItem"]["configurationItemStatus"]
    )
    assert (
        parsed_event.invoking_event.configuration_item.resource_type
        == invoking_event["configurationItem"]["resourceType"]
    )
    assert (
        parsed_event.invoking_event.configuration_item.resource_id == invoking_event["configurationItem"]["resourceId"]
    )
    assert (
        parsed_event.invoking_event.configuration_item.resource_name
        == invoking_event["configurationItem"]["resourceName"]
    )
    assert parsed_event.invoking_event.configuration_item.resource_arn == invoking_event["configurationItem"]["ARN"]
    assert parsed_event.invoking_event.configuration_item.region == invoking_event["configurationItem"]["awsRegion"]
    assert (
        parsed_event.invoking_event.configuration_item.availability_zone
        == invoking_event["configurationItem"]["availabilityZone"]
    )
    assert (
        parsed_event.invoking_event.configuration_item.configuration_state_md5_hash
        == invoking_event["configurationItem"]["configurationStateMd5Hash"]
    )
    assert (
        parsed_event.invoking_event.configuration_item.resource_creation_time
        == invoking_event["configurationItem"]["resourceCreationTime"]
    )


def test_aws_config_rule_oversized_configuration():
    """Check AWS Config OversizedConfigurationItemChangeNotification event"""

    raw_event = load_event("awsConfigRuleOversizedConfiguration.json")
    parsed_event = AWSConfigRuleEvent(raw_event)

    invoking_event = json.loads(raw_event["invokingEvent"])

    assert parsed_event.rule_parameters == json.loads(raw_event["ruleParameters"])
    assert parsed_event.raw_invoking_event == raw_event["invokingEvent"]
    assert parsed_event.result_token == raw_event["resultToken"]
    assert parsed_event.event_left_scope == raw_event["eventLeftScope"]
    assert parsed_event.execution_role_arn == raw_event["executionRoleArn"]
    assert parsed_event.config_rule_arn == raw_event["configRuleArn"]
    assert parsed_event.config_rule_name == raw_event["configRuleName"]
    assert parsed_event.config_rule_id == raw_event["configRuleId"]
    assert parsed_event.accountid == raw_event["accountId"]
    assert parsed_event.version == raw_event["version"]
    assert parsed_event.invoking_event.message_type == invoking_event["messageType"]
    assert parsed_event.invoking_event.notification_creation_time == invoking_event["notificationCreationTime"]
    assert parsed_event.invoking_event.record_version == invoking_event["recordVersion"]
    assert parsed_event.invoking_event.raw_configuration_item_summary == invoking_event["configurationItemSummary"]
    assert (
        parsed_event.invoking_event.configuration_item_summary.change_type
        == invoking_event["configurationItemSummary"]["changeType"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.configuration_item_version
        == invoking_event["configurationItemSummary"]["configurationItemVersion"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.configuration_item_capture_time
        == invoking_event["configurationItemSummary"]["configurationItemCaptureTime"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.configuration_state_id
        == invoking_event["configurationItemSummary"]["configurationStateId"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.accountid
        == invoking_event["configurationItemSummary"]["awsAccountId"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.configuration_item_status
        == invoking_event["configurationItemSummary"]["configurationItemStatus"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.resource_type
        == invoking_event["configurationItemSummary"]["resourceType"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.resource_id
        == invoking_event["configurationItemSummary"]["resourceId"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.resource_name
        == invoking_event["configurationItemSummary"]["resourceName"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.resource_arn
        == invoking_event["configurationItemSummary"]["ARN"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.region
        == invoking_event["configurationItemSummary"]["awsRegion"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.availability_zone
        == invoking_event["configurationItemSummary"]["availabilityZone"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.configuration_state_md5_hash
        == invoking_event["configurationItemSummary"]["configurationStateMd5Hash"]
    )
    assert (
        parsed_event.invoking_event.configuration_item_summary.resource_creation_time
        == invoking_event["configurationItemSummary"]["resourceCreationTime"]
    )


def test_aws_config_rule_scheduled():
    """Check AWS Config ScheduledNotification event"""

    raw_event = load_event("awsConfigRuleScheduled.json")
    parsed_event = AWSConfigRuleEvent(raw_event)

    invoking_event = json.loads(raw_event["invokingEvent"])

    assert parsed_event.rule_parameters == json.loads(raw_event["ruleParameters"])
    assert parsed_event.raw_invoking_event == raw_event["invokingEvent"]
    assert parsed_event.result_token == raw_event["resultToken"]
    assert parsed_event.event_left_scope == raw_event["eventLeftScope"]
    assert parsed_event.execution_role_arn == raw_event["executionRoleArn"]
    assert parsed_event.config_rule_arn == raw_event["configRuleArn"]
    assert parsed_event.config_rule_name == raw_event["configRuleName"]
    assert parsed_event.config_rule_id == raw_event["configRuleId"]
    assert parsed_event.accountid == raw_event["accountId"]
    assert parsed_event.version == raw_event["version"]
    assert parsed_event.evalution_mode == raw_event["evaluationMode"]
    assert parsed_event.invoking_event.message_type == invoking_event["messageType"]
    assert parsed_event.invoking_event.accountid == invoking_event["awsAccountId"]
    assert parsed_event.invoking_event.notification_creation_time == invoking_event["notificationCreationTime"]
    assert parsed_event.invoking_event.message_type == invoking_event["messageType"]
    assert parsed_event.invoking_event.record_version == invoking_event["recordVersion"]
