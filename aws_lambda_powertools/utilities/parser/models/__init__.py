from aws_lambda_powertools.shared.functions import disable_pydantic_v2_warning

disable_pydantic_v2_warning()

from .alb import AlbModel, AlbRequestContext, AlbRequestContextData  # noqa: E402
from .apigw import (  # noqa: E402
    APIGatewayEventAuthorizer,
    APIGatewayEventIdentity,
    APIGatewayEventRequestContext,
    APIGatewayProxyEventModel,
)
from .apigwv2 import (  # noqa: E402
    APIGatewayProxyEventV2Model,
    RequestContextV2,
    RequestContextV2Authorizer,
    RequestContextV2AuthorizerIam,
    RequestContextV2AuthorizerIamCognito,
    RequestContextV2AuthorizerJwt,
    RequestContextV2Http,
)
from .cloudformation_custom_resource import (  # noqa: E402
    CloudFormationCustomResourceBaseModel,
    CloudFormationCustomResourceCreateModel,
    CloudFormationCustomResourceDeleteModel,
    CloudFormationCustomResourceUpdateModel,
)
from .cloudwatch import (  # noqa: E402
    CloudWatchLogsData,
    CloudWatchLogsDecode,
    CloudWatchLogsLogEvent,
    CloudWatchLogsModel,
)
from .dynamodb import (  # noqa: E402
    DynamoDBStreamChangedRecordModel,
    DynamoDBStreamModel,
    DynamoDBStreamRecordModel,
)
from .event_bridge import EventBridgeModel  # noqa: E402
from .kafka import (  # noqa: E402
    KafkaBaseEventModel,
    KafkaMskEventModel,
    KafkaRecordModel,
    KafkaSelfManagedEventModel,
)
from .kinesis import (  # noqa: E402
    KinesisDataStreamModel,
    KinesisDataStreamRecord,
    KinesisDataStreamRecordPayload,
)
from .kinesis_firehose import (  # noqa: E402
    KinesisFirehoseModel,
    KinesisFirehoseRecord,
    KinesisFirehoseRecordMetadata,
)
from .kinesis_firehose_sqs import KinesisFirehoseSqsModel, KinesisFirehoseSqsRecord  # noqa: E402
from .lambda_function_url import LambdaFunctionUrlModel  # noqa: E402
from .s3 import (  # noqa: E402
    S3EventNotificationEventBridgeDetailModel,
    S3EventNotificationEventBridgeModel,
    S3EventNotificationObjectModel,
    S3Model,
    S3RecordModel,
)
from .s3_event_notification import (  # noqa: E402
    S3SqsEventNotificationModel,
    S3SqsEventNotificationRecordModel,
)
from .s3_object_event import (  # noqa: E402
    S3ObjectConfiguration,
    S3ObjectContext,
    S3ObjectLambdaEvent,
    S3ObjectSessionAttributes,
    S3ObjectSessionContext,
    S3ObjectSessionIssuer,
    S3ObjectUserIdentity,
    S3ObjectUserRequest,
)
from .ses import (  # noqa: E402
    SesMail,
    SesMailCommonHeaders,
    SesMailHeaders,
    SesMessage,
    SesModel,
    SesReceipt,
    SesReceiptAction,
    SesReceiptVerdict,
    SesRecordModel,
)
from .sns import SnsModel, SnsNotificationModel, SnsRecordModel  # noqa: E402
from .sqs import SqsAttributesModel, SqsModel, SqsMsgAttributeModel, SqsRecordModel  # noqa: E402
from .vpc_lattice import VpcLatticeModel  # noqa: E402

__all__ = [
    "APIGatewayProxyEventV2Model",
    "RequestContextV2",
    "RequestContextV2Http",
    "RequestContextV2Authorizer",
    "RequestContextV2AuthorizerJwt",
    "RequestContextV2AuthorizerIam",
    "RequestContextV2AuthorizerIamCognito",
    "CloudWatchLogsData",
    "CloudWatchLogsDecode",
    "CloudWatchLogsLogEvent",
    "CloudWatchLogsModel",
    "AlbModel",
    "AlbRequestContext",
    "AlbRequestContextData",
    "DynamoDBStreamModel",
    "EventBridgeModel",
    "DynamoDBStreamChangedRecordModel",
    "DynamoDBStreamRecordModel",
    "DynamoDBStreamChangedRecordModel",
    "KinesisDataStreamModel",
    "KinesisDataStreamRecord",
    "KinesisDataStreamRecordPayload",
    "KinesisFirehoseModel",
    "KinesisFirehoseRecord",
    "KinesisFirehoseRecordMetadata",
    "LambdaFunctionUrlModel",
    "S3Model",
    "S3RecordModel",
    "S3ObjectLambdaEvent",
    "S3ObjectUserIdentity",
    "S3ObjectSessionContext",
    "S3ObjectSessionAttributes",
    "S3ObjectSessionIssuer",
    "S3ObjectUserRequest",
    "S3ObjectConfiguration",
    "S3ObjectContext",
    "S3EventNotificationObjectModel",
    "S3EventNotificationEventBridgeModel",
    "S3EventNotificationEventBridgeDetailModel",
    "SesModel",
    "SesRecordModel",
    "SesMessage",
    "SesMail",
    "SesMailCommonHeaders",
    "SesMailHeaders",
    "SesReceipt",
    "SesReceiptAction",
    "SesReceiptVerdict",
    "SnsModel",
    "SnsNotificationModel",
    "SnsRecordModel",
    "SqsModel",
    "SqsRecordModel",
    "SqsMsgAttributeModel",
    "SqsAttributesModel",
    "S3SqsEventNotificationModel",
    "S3SqsEventNotificationRecordModel",
    "APIGatewayProxyEventModel",
    "APIGatewayEventRequestContext",
    "APIGatewayEventAuthorizer",
    "APIGatewayEventIdentity",
    "KafkaSelfManagedEventModel",
    "KafkaRecordModel",
    "KafkaMskEventModel",
    "KafkaBaseEventModel",
    "KinesisFirehoseSqsModel",
    "KinesisFirehoseSqsRecord",
    "CloudFormationCustomResourceUpdateModel",
    "CloudFormationCustomResourceDeleteModel",
    "CloudFormationCustomResourceCreateModel",
    "CloudFormationCustomResourceBaseModel",
    "VpcLatticeModel",
]
