import pytest

from aws_lambda_powertools.event_handler.async_execution.routes.secrets_manager import SecretsManagerRoute
from aws_lambda_powertools.utilities.data_classes.secrets_manager_event import SecretsManagerEvent
from tests.functional.utils import load_event


class TestSecretsManagerRoute:
    def test_constructor_error(self):
        with pytest.raises(ValueError):
            SecretsManagerRoute(func=lambda _: None)

    @pytest.mark.parametrize(
        "event_name, option_constructor, is_match",
        [
            # with secret_id and secret_name_prefix
            # match all
            (
                "secretsManagerEvent.json",
                {
                    "func": lambda *_: None,
                    "secret_id": "arn:aws:secretsmanager:us-west-2:123456789012:secret:MyTestDatabaseSecret-a1b2c3",
                    "secret_name_prefix": "MyTestDatabaseSecret",
                },
                True,
            ),
            # with secret_id and secret_name_prefix
            # match 1, unmatch 1
            (
                "secretsManagerEvent.json",
                {
                    "func": lambda *_: None,
                    "secret_id": "arn:aws:secretsmanager:us-west-2:123456789012:secret:MyTestDatabaseSecret-a1b2c3",
                    "secret_name_prefix": "MyTestDatabaseSecretV2",
                },
                False,
            ),
            (
                "secretsManagerEvent.json",
                {
                    "func": lambda *_: None,
                    "secret_id": "arn:aws:secretsmanager:us-west-2:123456789012:secret:MyTestDatabaseSecret-999999",
                    "secret_name_prefix": "MyTestDatabaseSecret",
                },
                False,
            ),
            # with secret_id and secret_name_prefix
            # unmatch all
            (
                "secretsManagerEvent.json",
                {
                    "func": lambda *_: None,
                    "secret_id": "arn:aws:secretsmanager:us-west-2:123456789012:secret:MyTestDatabaseSecret-999999",
                    "secret_name_prefix": "MyTestDatabaseSecretV2",
                },
                False,
            ),
            # with secret_id
            (
                "secretsManagerEvent.json",
                {
                    "func": lambda *_: None,
                    "secret_id": "arn:aws:secretsmanager:us-west-2:123456789012:secret:MyTestDatabaseSecret-a1b2c3",
                },
                True,
            ),
            (
                "secretsManagerEvent.json",
                {
                    "func": lambda *_: None,
                    "secret_id": "arn:aws:secretsmanager:us-west-2:123456789012:secret:MyTestDatabaseSecret-999999",
                },
                False,
            ),
            # with secret_name_prefix
            ("secretsManagerEvent.json", {"func": lambda *_: None, "secret_name_prefix": "MyTestDatabaseSecret"}, True),
            (
                "secretsManagerEvent.json",
                {"func": lambda *_: None, "secret_name_prefix": "MyTestDatabaseSecretV2"},
                False,
            ),
        ],
    )
    def test_match(self, event_name, option_constructor, is_match):
        event = load_event(file_name=event_name)
        route = SecretsManagerRoute(**option_constructor)
        actual = route.match(event=event)
        if is_match:
            expected = (route.func, SecretsManagerEvent(event))
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
            "eventBridgeEvent.json",
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
    def test_match_for_not_secrets_manager_event(self, event_name):
        event = load_event(file_name=event_name)
        route = SecretsManagerRoute(
            func=None,
            secret_id="arn:aws:secretsmanager:us-west-2:123456789012:secret:MyTestDatabaseSecret-a1b2c3",
        )
        actual = route.match(event=event)
        assert actual is None
