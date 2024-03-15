from pathlib import Path

from aws_cdk import CfnOutput, Duration, Expiration
from aws_cdk import aws_appsync_alpha as appsync
from aws_cdk.aws_lambda import Function

from tests.e2e.utils.data_builder import build_random_value
from tests.e2e.utils.infrastructure import BaseInfrastructure


class EventHandlerAppSyncStack(BaseInfrastructure):
    def create_resources(self):
        functions = self.create_lambda_functions()

        self._create_appsync_endpoint(function=functions["AppsyncResolverHandler"])

    def _create_appsync_endpoint(self, function: Function):
        api = appsync.GraphqlApi(
            self.stack,
            "Api",
            name=f"e2e-tests{build_random_value()}",
            schema=appsync.SchemaFile.from_asset(str(Path(self.feature_path, "files/schema.graphql"))),
            authorization_config=appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(
                    authorization_type=appsync.AuthorizationType.API_KEY,
                    api_key_config=appsync.ApiKeyConfig(
                        description="public key for getting data",
                        expires=Expiration.after(Duration.hours(25)),
                        name="API Token",
                    ),
                ),
            ),
            xray_enabled=False,
        )
        lambda_datasource = api.add_lambda_data_source("DataSource", lambda_function=function)

        lambda_datasource.create_resolver(
            "QueryGetAllPostsResolver",
            type_name="Query",
            field_name="allPosts",
        )
        lambda_datasource.create_resolver(
            "QueryGetPostResolver",
            type_name="Query",
            field_name="getPost",
        )
        lambda_datasource.create_resolver(
            "QueryGetPostRelatedResolver",
            type_name="Post",
            field_name="relatedPosts",
            max_batch_size=10,
        )

        lambda_datasource.create_resolver(
            "QueryGetPostRelatedAsyncResolver",
            type_name="Post",
            field_name="relatedPostsAsync",
            max_batch_size=10,
        )

        CfnOutput(self.stack, "GraphQLHTTPUrl", value=api.graphql_url)
        CfnOutput(self.stack, "GraphQLAPIKey", value=api.api_key)
