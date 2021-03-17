from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.typing.lambda_client_context import LambdaClientContext
from aws_lambda_powertools.utilities.typing.lambda_client_context_mobile_client import LambdaClientContextMobileClient
from aws_lambda_powertools.utilities.typing.lambda_cognito_identity import LambdaCognitoIdentity


def test_typing():
    context = LambdaContext()
    context._function_name = "_function_name"
    context._function_version = "_function_version"
    context._invoked_function_arn = "_invoked_function_arn"
    context._memory_limit_in_mb = "_memory_limit_in_mb"
    context._aws_request_id = "_aws_request_id"
    context._log_group_name = "_log_group_name"
    context._log_stream_name = "_log_stream_name"
    identity = LambdaCognitoIdentity()
    identity._cognito_identity_id = "_cognito_identity_id"
    identity._cognito_identity_pool_id = "_cognito_identity_pool_id"
    context._identity = identity
    client_context = LambdaClientContext()
    client = LambdaClientContextMobileClient()
    client._installation_id = "_installation_id"
    client._app_title = "_app_title"
    client._app_version_name = "_app_version_name"
    client._app_version_code = "_app_version_code"
    client._app_package_name = "_app_package_name"
    client_context._client = client
    client_context._custom = {}
    client_context._env = {}
    context._client_context = client_context

    assert context.function_name == context._function_name
    assert context.function_version == context._function_version
    assert context.invoked_function_arn == context._invoked_function_arn
    assert context.memory_limit_in_mb == context._memory_limit_in_mb
    assert context.aws_request_id == context._aws_request_id
    assert context.log_group_name == context._log_group_name
    assert context.log_stream_name == context._log_stream_name
    assert context.identity == context._identity
    assert context.identity.cognito_identity_id == identity._cognito_identity_id
    assert context.identity.cognito_identity_pool_id == identity._cognito_identity_pool_id
    assert context.client_context == context._client_context
    assert context.client_context.client == client_context._client
    assert context.client_context.client.installation_id == client._installation_id
    assert context.client_context.client.app_title == client._app_title
    assert context.client_context.client.app_version_name == client._app_version_name
    assert context.client_context.client.app_version_code == client._app_version_code
    assert context.client_context.client.app_package_name == client._app_package_name
    assert context.client_context.custom == client_context._custom
    assert context.client_context.env == client_context._env
    assert context.get_remaining_time_in_millis() == 0
