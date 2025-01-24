import pytest

from aws_lambda_powertools.event_handler.async_execution.routes.event_bridge import (
    EventBridgeRoute,
)
from aws_lambda_powertools.utilities.data_classes.event_bridge_event import (
    EventBridgeEvent,
)
from tests.functional.utils import load_event


class TestEventBridgeRoute:
    def test_constructor_error(self):
        with pytest.raises(ValueError):
            EventBridgeRoute(func=lambda *_: None)

    @pytest.mark.parametrize(
        "option_constructor, expected",
        [
            (
                {"func": None, "resources": "test"},
                {"func": None, "detail_type": None, "source": None, "resources": ["test"]},
            ),
            (
                {"func": None, "resources": ["test"]},
                {"func": None, "detail_type": None, "source": None, "resources": ["test"]},
            ),
            (
                {"func": None, "resources": ["test", "name"]},
                {"func": None, "detail_type": None, "source": None, "resources": ["test", "name"]},
            ),
        ],
    )
    def test_constructor_normal(self, option_constructor, expected):
        route = EventBridgeRoute(**option_constructor)
        assert route.__dict__ == expected

    @pytest.mark.parametrize(
        "option_constructor, option_func, expected",
        [
            # without detail_type at option_func
            ({"func": None, "detail_type": "test type"}, {"detail_type": None}, False),
            # without detail_type
            ({"func": None, "source": "aws.ec2"}, {"detail_type": "test type"}, False),
            # with detail_type
            ({"func": None, "detail_type": "test type"}, {"detail_type": "test type 2"}, False),
            ({"func": None, "detail_type": "test type"}, {"detail_type": "test type"}, True),
        ],
    )
    def test_is_target_with_detail_type(self, option_constructor, option_func, expected):
        route = EventBridgeRoute(**option_constructor)
        actual = route.is_target_with_detail_type(**option_func)
        assert actual == expected

    @pytest.mark.parametrize(
        "option_constructor, option_func, expected",
        [
            # without source at option_func
            ({"func": None, "source": "aws.ec2"}, {"source": None}, False),
            # without source
            ({"func": None, "detail_type": "test type"}, {"source": "aws.ec2"}, False),
            # with source
            ({"func": None, "source": "aws.ec2"}, {"source": "aws.lambda"}, False),
            ({"func": None, "source": "aws.ec2"}, {"source": "aws.ec2"}, True),
        ],
    )
    def test_is_target_with_source(self, option_constructor, option_func, expected):
        route = EventBridgeRoute(**option_constructor)
        actual = route.is_target_with_source(**option_func)
        assert actual == expected

    @pytest.mark.parametrize(
        "option_constructor, option_func, expected",
        [
            # without resources at option_func
            (
                {"func": None, "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"]},
                {"resources": None},
                False,
            ),
            # without resources
            (
                {"func": None, "source": "aws.ec2"},
                {"resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-9999999999abcdef9"]},
                False,
            ),
            # with resources
            (
                {"func": None, "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"]},
                {"resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-9999999999abcdef9"]},
                False,
            ),
            (
                {"func": None, "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"]},
                {"resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"]},
                True,
            ),
            (
                {
                    "func": None,
                    "resources": [
                        "arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0",
                        "arn:aws:ec2:us-west-1:123456789012:instance/i-2222222222abcdef2",
                    ],
                },
                {"resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"]},
                True,
            ),
            (
                {
                    "func": None,
                    "resources": [
                        "arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0",
                    ],
                },
                {
                    "resources": [
                        "arn:aws:ec2:us-west-1:123456789012:instance/i-2222222222abcdef2",
                        "arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0",
                    ],
                },
                True,
            ),
            (
                {
                    "func": None,
                    "resources": [
                        "arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0",
                        "arn:aws:ec2:us-west-1:123456789012:instance/i-3333333333abcdef3",
                    ],
                },
                {
                    "resources": [
                        "arn:aws:ec2:us-west-1:123456789012:instance/i-2222222222abcdef2",
                        "arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0",
                    ],
                },
                True,
            ),
        ],
    )
    def test_is_target_with_resources(self, option_constructor, option_func, expected):
        route = EventBridgeRoute(**option_constructor)
        actual = route.is_target_with_resources(**option_func)
        assert actual == expected

    @pytest.mark.parametrize(
        "event_name, option_constructor, is_match",
        [
            # with detail_type, source, resources
            # match all
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification",
                    "source": "aws.ec2",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"],
                },
                True,
            ),
            # with detail_type, source, resources
            # match 2, unmatch 1
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification",
                    "source": "aws.ec2",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-99999999999999999"],
                },
                False,
            ),
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification",
                    "source": "aws.lambda",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"],
                },
                False,
            ),
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification V2",
                    "source": "aws.ec2",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"],
                },
                False,
            ),
            # with detail_type, source, resources
            # match 1, unmatch 2
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification",
                    "source": "aws.lambda",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-99999999999999999"],
                },
                False,
            ),
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification V2",
                    "source": "aws.ec2",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-99999999999999999"],
                },
                False,
            ),
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification V2",
                    "source": "aws.lambda",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"],
                },
                False,
            ),
            # with detail_type, source, resources
            # unmatch all
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification V2",
                    "source": "aws.lambda",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-99999999999999999"],
                },
                False,
            ),
            # with detail_type and source
            # match all
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification",
                    "source": "aws.ec2",
                },
                True,
            ),
            # with detail_type and source
            # match 1, unmatch 1
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification",
                    "source": "aws.lambda",
                },
                False,
            ),
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification V2",
                    "source": "aws.ec2",
                },
                False,
            ),
            # with detail_type and source
            # unmatch all
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification V2",
                    "source": "aws.lambda",
                },
                False,
            ),
            # with detail_type and resources
            # match all
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"],
                },
                True,
            ),
            # with detail_type and resources
            # match 1, unmatch 1
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-99999999999999999"],
                },
                False,
            ),
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification V2",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"],
                },
                False,
            ),
            # with detail_type and resources
            # unmatch all
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification V2",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-99999999999999999"],
                },
                False,
            ),
            # with source and resources
            # match all
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "source": "aws.ec2",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"],
                },
                True,
            ),
            # with source and resources
            # match 1, unmatch 1
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "source": "aws.ec2",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-99999999999999999"],
                },
                False,
            ),
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "source": "aws.lambda",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"],
                },
                False,
            ),
            # with source and resources
            # unmatch all
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "source": "aws.lambda",
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-99999999999999999"],
                },
                False,
            ),
            # with detail_type
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification",
                },
                True,
            ),
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "detail_type": "EC2 Instance State-change Notification V2",
                },
                False,
            ),
            # with source
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "source": "aws.ec2",
                },
                True,
            ),
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "source": "aws.lambda",
                },
                False,
            ),
            # with resources
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"],
                },
                True,
            ),
            (
                "eventBridgeEvent.json",
                {
                    "func": lambda *_: None,
                    "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-99999999999999999"],
                },
                False,
            ),
        ],
    )
    def test_match_for_event_bridge_event(self, event_name, option_constructor, is_match):
        event = load_event(file_name=event_name)
        route = EventBridgeRoute(**option_constructor)
        actual = route.match(event=event)
        if is_match:
            expected = route.func, EventBridgeEvent(event)
            assert actual == expected
        else:
            assert actual is None

    @pytest.mark.parametrize(
        "event_name",
        [
            "activeMQEvent.json",
            "albEvent.json",
            "albEventPathTrailingSlash.json",
            "albMultiValueHeadersEvent.json",
            "albMultiValueQueryStringEvent.json",
            "apiGatewayAuthorizerRequestEvent.json",
            "apiGatewayAuthorizerTokenEvent.json",
            "apiGatewayAuthorizerV2Event.json",
            "apiGatewayProxyEvent.json",
            "apiGatewayProxyEventAnotherPath.json",
            "apiGatewayProxyEventNoOrigin.json",
            "apiGatewayProxyEventPathTrailingSlash.json",
            "apiGatewayProxyEventPrincipalId.json",
            "apiGatewayProxyEvent_noVersionAuth.json",
            "apiGatewayProxyOtherEvent.json",
            "apiGatewayProxyV2Event.json",
            "apiGatewayProxyV2EventPathTrailingSlash.json",
            "apiGatewayProxyV2Event_GET.json",
            "apiGatewayProxyV2IamEvent.json",
            "apiGatewayProxyV2LambdaAuthorizerEvent.json",
            "apiGatewayProxyV2OtherGetEvent.json",
            "apiGatewayProxyV2SchemaMiddlwareInvalidEvent.json",
            "apiGatewayProxyV2SchemaMiddlwareValidEvent.json",
            "apigatewayeSchemaMiddlwareInvalidEvent.json",
            "apigatewayeSchemaMiddlwareValidEvent.json",
            "appSyncAuthorizerEvent.json",
            "appSyncAuthorizerResponse.json",
            "appSyncBatchEvent.json",
            "appSyncDirectResolver.json",
            "appSyncResolverEvent.json",
            "awsConfigRuleConfigurationChanged.json",
            "awsConfigRuleOversizedConfiguration.json",
            "awsConfigRuleScheduled.json",
            "bedrockAgentEvent.json",
            "bedrockAgentEventWithPathParams.json",
            "bedrockAgentPostEvent.json",
            "cloudWatchAlarmEventCompositeMetric.json",
            "cloudWatchAlarmEventSingleMetric.json",
            "cloudWatchDashboardEvent.json",
            "cloudWatchLogEvent.json",
            "cloudWatchLogEventWithPolicyLevel.json",
            "cloudformationCustomResourceCreate.json",
            "cloudformationCustomResourceDelete.json",
            "cloudformationCustomResourceUpdate.json",
            "codeDeployLifecycleHookEvent.json",
            "codePipelineEvent.json",
            "codePipelineEventData.json",
            "codePipelineEventEmptyUserParameters.json",
            "codePipelineEventWithEncryptionKey.json",
            "cognitoCreateAuthChallengeEvent.json",
            "cognitoCustomEmailSenderEvent.json",
            "cognitoCustomMessageEvent.json",
            "cognitoCustomSMSSenderEvent.json",
            "cognitoDefineAuthChallengeEvent.json",
            "cognitoPostAuthenticationEvent.json",
            "cognitoPostConfirmationEvent.json",
            "cognitoPreAuthenticationEvent.json",
            "cognitoPreSignUpEvent.json",
            "cognitoPreTokenGenerationEvent.json",
            "cognitoPreTokenV2GenerationEvent.json",
            "cognitoUserMigrationEvent.json",
            "cognitoVerifyAuthChallengeResponseEvent.json",
            "connectContactFlowEventAll.json",
            "connectContactFlowEventMin.json",
            "dynamoStreamEvent.json",
            "kafkaEventMsk.json",
            "kafkaEventSelfManaged.json",
            "kinesisFirehoseKinesisEvent.json",
            "kinesisFirehosePutEvent.json",
            "kinesisFirehoseSQSEvent.json",
            "kinesisStreamCloudWatchLogsEvent.json",
            "kinesisStreamEvent.json",
            "kinesisStreamEventOneRecord.json",
            "lambdaFunctionUrlEvent.json",
            "lambdaFunctionUrlEventPathTrailingSlash.json",
            "lambdaFunctionUrlEventWithHeaders.json",
            "lambdaFunctionUrlIAMEvent.json",
            "rabbitMQEvent.json",
            "s3BatchOperationEventSchemaV1.json",
            "s3BatchOperationEventSchemaV2.json",
            "s3Event.json",
            "s3EventBridgeNotificationObjectCreatedEvent.json",
            "s3EventBridgeNotificationObjectDeletedEvent.json",
            "s3EventBridgeNotificationObjectExpiredEvent.json",
            "s3EventBridgeNotificationObjectRestoreCompletedEvent.json",
            "s3EventDecodedKey.json",
            "s3EventDeleteObject.json",
            "s3EventGlacier.json",
            "s3ObjectEventIAMUser.json",
            "s3ObjectEventTempCredentials.json",
            "s3SqsEvent.json",
            "secretsManagerEvent.json",
            "sesEvent.json",
            "snsEvent.json",
            "snsSqsEvent.json",
            "snsSqsFifoEvent.json",
            "sqsDlqTriggerEvent.json",
            "sqsEvent.json",
            "vpcLatticeEvent.json",
            "vpcLatticeEventPathTrailingSlash.json",
            "vpcLatticeEventV2PathTrailingSlash.json",
            "vpcLatticeV2Event.json",
            "vpcLatticeV2EventWithHeaders.json",
        ],
    )
    def test_match_for_not_event_bridge_event(self, event_name):
        event = load_event(file_name=event_name)
        route = EventBridgeRoute(func=None, detail_type="EC2 Instance State-change Notification")
        actual = route.match(event=event)
        assert actual is None
