"""
Event Source Data Classes utility provides classes self-describing Lambda event sources.
"""

from .alb_event import ALBEvent
from .api_gateway_proxy_event import APIGatewayProxyEvent, APIGatewayProxyEventV2
from .appsync_resolver_event import AppSyncResolverEvent
from .aws_config_rule_event import AWSConfigRuleEvent
from .cloud_watch_custom_widget_event import CloudWatchDashboardCustomWidgetEvent
from .cloud_watch_logs_event import CloudWatchLogsEvent
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
from .s3_event import S3Event, S3EventBridgeNotificationEvent
from .secrets_manager_event import SecretsManagerEvent
from .ses_event import SESEvent
from .sns_event import SNSEvent
from .sqs_event import SQSEvent
from .vpc_lattice import VPCLatticeEvent

__all__ = [
    "APIGatewayProxyEvent",
    "APIGatewayProxyEventV2",
    "SecretsManagerEvent",
    "AppSyncResolverEvent",
    "ALBEvent",
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
    "SESEvent",
    "SNSEvent",
    "SQSEvent",
    "event_source",
    "AWSConfigRuleEvent",
    "VPCLatticeEvent",
]
