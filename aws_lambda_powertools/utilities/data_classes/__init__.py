"""
Event Source Data Classes utility provides classes self-describing Lambda event sources.
"""

from .alb_event import ALBEvent
from .api_gateway_proxy_event import APIGatewayProxyEvent, APIGatewayProxyEventV2
from .appsync_resolver_event import AppSyncResolverEvent
from .cloud_watch_logs_event import CloudWatchLogsEvent
from .code_pipeline_job_event import CodePipelineJobEvent
from .connect_contact_flow_event import ConnectContactFlowEvent
from .dynamo_db_stream_event import DynamoDBStreamEvent
from .event_bridge_event import EventBridgeEvent
from .event_source import event_source
from .kinesis_stream_event import KinesisStreamEvent
from .s3_event import S3Event
from .ses_event import SESEvent
from .sns_event import SNSEvent
from .sqs_event import SQSEvent

__all__ = [
    "APIGatewayProxyEvent",
    "APIGatewayProxyEventV2",
    "AppSyncResolverEvent",
    "ALBEvent",
    "CloudWatchLogsEvent",
    "CodePipelineJobEvent",
    "ConnectContactFlowEvent",
    "DynamoDBStreamEvent",
    "EventBridgeEvent",
    "KinesisStreamEvent",
    "S3Event",
    "SESEvent",
    "SNSEvent",
    "SQSEvent",
    "event_source",
]
