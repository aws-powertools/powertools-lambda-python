import json

from aws_lambda_powertools.utilities.data_classes import AWSConfigRuleEvent
from tests.functional.utils import load_event


def test_aws_config_rule_configuration_changed():
    """Check AWS Config ConfigurationItemChangeNotification event"""
    event = AWSConfigRuleEvent(load_event("awsConfigRuleConfigurationChanged.json"))

    invoking_event = json.loads(event["invokingEvent"])

    assert event.rule_parameters == json.loads(event["ruleParameters"])
    assert event.raw_invoking_event == event["invokingEvent"]
    assert event.result_token == event["resultToken"]
    assert event.event_left_scope == event["eventLeftScope"]
    assert event.execution_role_arn == event["executionRoleArn"]
    assert event.config_rule_arn == event["configRuleArn"]
    assert event.config_rule_name == event["configRuleName"]
    assert event.config_rule_id == event["configRuleId"]
    assert event.accountid == event["accountId"]
    assert event.version == event["version"]
    assert event.evalution_mode == event["evaluationMode"]
    assert event.invoking_event.message_type == invoking_event["messageType"]
    assert event.invoking_event.raw_configuration_item == invoking_event["configurationItem"]
    assert event.invoking_event.record_version == invoking_event["recordVersion"]
    assert event.invoking_event.notification_creation_time == invoking_event["notificationCreationTime"]
    assert event.invoking_event.configuration_item_diff == invoking_event["configurationItemDiff"]
    assert (
        event.invoking_event.configuration_item.related_events == invoking_event["configurationItem"]["relatedEvents"]
    )
    assert event.invoking_event.configuration_item.relationships == invoking_event["configurationItem"]["relationships"]
    assert event.invoking_event.configuration_item.configuration == invoking_event["configurationItem"]["configuration"]
    assert (
        event.invoking_event.configuration_item.supplementary_configuration
        == invoking_event["configurationItem"]["supplementaryConfiguration"]
    )
    assert event.invoking_event.configuration_item.tags == invoking_event["configurationItem"]["tags"]
    assert (
        event.invoking_event.configuration_item.configuration_item_version
        == invoking_event["configurationItem"]["configurationItemVersion"]
    )
    assert (
        event.invoking_event.configuration_item.configuration_item_capture_time
        == invoking_event["configurationItem"]["configurationItemCaptureTime"]
    )
    assert (
        event.invoking_event.configuration_item.configuration_state_id
        == invoking_event["configurationItem"]["configurationStateId"]
    )
    assert event.invoking_event.configuration_item.accountid == invoking_event["configurationItem"]["awsAccountId"]
    assert (
        event.invoking_event.configuration_item.configuration_item_status
        == invoking_event["configurationItem"]["configurationItemStatus"]
    )
    assert event.invoking_event.configuration_item.resource_type == invoking_event["configurationItem"]["resourceType"]
    assert event.invoking_event.configuration_item.resource_id == invoking_event["configurationItem"]["resourceId"]
    assert event.invoking_event.configuration_item.resource_name == invoking_event["configurationItem"]["resourceName"]
    assert event.invoking_event.configuration_item.resource_arn == invoking_event["configurationItem"]["ARN"]
    assert event.invoking_event.configuration_item.region == invoking_event["configurationItem"]["awsRegion"]
    assert (
        event.invoking_event.configuration_item.availability_zone
        == invoking_event["configurationItem"]["availabilityZone"]
    )
    assert (
        event.invoking_event.configuration_item.configuration_state_md5_hash
        == invoking_event["configurationItem"]["configurationStateMd5Hash"]
    )
    assert (
        event.invoking_event.configuration_item.resource_creation_time
        == invoking_event["configurationItem"]["resourceCreationTime"]
    )


def test_aws_config_rule_oversized_configuration():
    """Check AWS Config OversizedConfigurationItemChangeNotification event"""
    event = AWSConfigRuleEvent(load_event("awsConfigRuleOversizedConfiguration.json"))

    invoking_event = json.loads(event["invokingEvent"])

    assert event.rule_parameters == json.loads(event["ruleParameters"])
    assert event.raw_invoking_event == event["invokingEvent"]
    assert event.result_token == event["resultToken"]
    assert event.event_left_scope == event["eventLeftScope"]
    assert event.execution_role_arn == event["executionRoleArn"]
    assert event.config_rule_arn == event["configRuleArn"]
    assert event.config_rule_name == event["configRuleName"]
    assert event.config_rule_id == event["configRuleId"]
    assert event.accountid == event["accountId"]
    assert event.version == event["version"]
    assert event.invoking_event.message_type == invoking_event["messageType"]
    assert event.invoking_event.notification_creation_time == invoking_event["notificationCreationTime"]
    assert event.invoking_event.record_version == invoking_event["recordVersion"]
    assert event.invoking_event.raw_configuration_item_summary == invoking_event["configurationItemSummary"]
    assert (
        event.invoking_event.configuration_item_summary.change_type
        == invoking_event["configurationItemSummary"]["changeType"]
    )
    assert (
        event.invoking_event.configuration_item_summary.configuration_item_version
        == invoking_event["configurationItemSummary"]["configurationItemVersion"]
    )
    assert (
        event.invoking_event.configuration_item_summary.configuration_item_capture_time
        == invoking_event["configurationItemSummary"]["configurationItemCaptureTime"]
    )
    assert (
        event.invoking_event.configuration_item_summary.configuration_state_id
        == invoking_event["configurationItemSummary"]["configurationStateId"]
    )
    assert (
        event.invoking_event.configuration_item_summary.accountid
        == invoking_event["configurationItemSummary"]["awsAccountId"]
    )
    assert (
        event.invoking_event.configuration_item_summary.configuration_item_status
        == invoking_event["configurationItemSummary"]["configurationItemStatus"]
    )
    assert (
        event.invoking_event.configuration_item_summary.resource_type
        == invoking_event["configurationItemSummary"]["resourceType"]
    )
    assert (
        event.invoking_event.configuration_item_summary.resource_id
        == invoking_event["configurationItemSummary"]["resourceId"]
    )
    assert (
        event.invoking_event.configuration_item_summary.resource_name
        == invoking_event["configurationItemSummary"]["resourceName"]
    )
    assert (
        event.invoking_event.configuration_item_summary.resource_arn
        == invoking_event["configurationItemSummary"]["ARN"]
    )
    assert (
        event.invoking_event.configuration_item_summary.region
        == invoking_event["configurationItemSummary"]["awsRegion"]
    )
    assert (
        event.invoking_event.configuration_item_summary.availability_zone
        == invoking_event["configurationItemSummary"]["availabilityZone"]
    )
    assert (
        event.invoking_event.configuration_item_summary.configuration_state_md5_hash
        == invoking_event["configurationItemSummary"]["configurationStateMd5Hash"]
    )
    assert (
        event.invoking_event.configuration_item_summary.resource_creation_time
        == invoking_event["configurationItemSummary"]["resourceCreationTime"]
    )


def test_aws_config_rule_scheduled():
    """Check AWS Config ScheduledNotification event"""
    event = AWSConfigRuleEvent(load_event("awsConfigRuleScheduled.json"))

    invoking_event = json.loads(event["invokingEvent"])

    assert event.rule_parameters == json.loads(event["ruleParameters"])
    assert event.raw_invoking_event == event["invokingEvent"]
    assert event.result_token == event["resultToken"]
    assert event.event_left_scope == event["eventLeftScope"]
    assert event.execution_role_arn == event["executionRoleArn"]
    assert event.config_rule_arn == event["configRuleArn"]
    assert event.config_rule_name == event["configRuleName"]
    assert event.config_rule_id == event["configRuleId"]
    assert event.accountid == event["accountId"]
    assert event.version == event["version"]
    assert event.evalution_mode == event["evaluationMode"]
    assert event.invoking_event.message_type == invoking_event["messageType"]
    assert event.invoking_event.accountid == invoking_event["awsAccountId"]
    assert event.invoking_event.notification_creation_time == invoking_event["notificationCreationTime"]
    assert event.invoking_event.message_type == invoking_event["messageType"]
    assert event.invoking_event.record_version == invoking_event["recordVersion"]
