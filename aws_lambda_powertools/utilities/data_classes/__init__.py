"""
Event Source Data Classes utility provides classes self-describing Lambda event sources.
"""

from .alb_event import ALBEvent
from .api_gateway_proxy_event import APIGatewayProxyEvent, APIGatewayProxyEventV2
from .appsync_resolver_event import AppSyncResolverEvent
from .aws_config_rule_event import AWSConfigRuleEvent
from .bedrock_agent_event import BedrockAgentEvent
from .cloud_watch_alarm_event import (
    CloudWatchAlarmConfiguration,
    CloudWatchAlarmData,
    CloudWatchAlarmEvent,
    CloudWatchAlarmMetric,
    CloudWatchAlarmMetricStat,
    CloudWatchAlarmState,
)
from .cloud_watch_custom_widget_event import CloudWatchDashboardCustomWidgetEvent
from .cloud_watch_logs_event import CloudWatchLogsEvent
from .cloudformation_custom_resource_event import CloudFormationCustomResourceEvent
from .code_pipeline_job_event import CodePipelineJobEvent
from .connect_contact_flow_event import ConnectContactFlowEvent
from .dynamo_db_stream_event import DynamoDBStreamEvent
from .event_bridge_event import EventBridgeEvent
from .event_source import event_source
from .kafka_event import KafkaEvent
from .kinesis_firehose_event import (
    KinesisFirehoseDataTransformationRecord,
    KinesisFirehoseDataTransformationRecordMetadata,
    KinesisFirehoseDataTransformationResponse,
    KinesisFirehoseEvent,
)
from .kinesis_stream_event import KinesisStreamEvent
from .lambda_function_url_event import LambdaFunctionUrlEvent
from .s3_batch_operation_event import (
    S3BatchOperationEvent,
    S3BatchOperationResponse,
    S3BatchOperationResponseRecord,
)
from .s3_event import S3Event, S3EventBridgeNotificationEvent
from .secrets_manager_event import SecretsManagerEvent
from .ses_event import SESEvent
from .sns_event import SNSEvent
from .sqs_event import SQSEvent
from .vpc_lattice import VPCLatticeEvent, VPCLatticeEventV2

__all__ = [
    "APIGatewayProxyEvent",
    "APIGatewayProxyEventV2",
    "SecretsManagerEvent",
    "AppSyncResolverEvent",
    "ALBEvent",
    "BedrockAgentEvent",
    "CloudWatchAlarmData",
    "CloudWatchAlarmEvent",
    "CloudWatchAlarmMetric",
    "CloudWatchAlarmState",
    "CloudWatchAlarmConfiguration",
    "CloudWatchAlarmMetricStat",
    "CloudWatchDashboardCustomWidgetEvent",
    "CloudWatchLogsEvent",
    "CodePipelineJobEvent",
    "ConnectContactFlowEvent",
    "DynamoDBStreamEvent",
    "EventBridgeEvent",
    "KafkaEvent",
    "KinesisFirehoseEvent",
    "KinesisStreamEvent",
    "KinesisFirehoseDataTransformationResponse",
    "KinesisFirehoseDataTransformationRecord",
    "KinesisFirehoseDataTransformationRecordMetadata",
    "LambdaFunctionUrlEvent",
    "S3Event",
    "S3EventBridgeNotificationEvent",
    "S3BatchOperationEvent",
    "S3BatchOperationResponse",
    "S3BatchOperationResponseRecord",
    "SESEvent",
    "SNSEvent",
    "SQSEvent",
    "event_source",
    "AWSConfigRuleEvent",
    "VPCLatticeEvent",
    "VPCLatticeEventV2",
    "CloudFormationCustomResourceEvent",
]
