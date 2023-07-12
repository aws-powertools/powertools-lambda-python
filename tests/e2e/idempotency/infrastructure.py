from aws_cdk import CfnOutput, RemovalPolicy
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk.aws_dynamodb import Table

from tests.e2e.utils.infrastructure import BaseInfrastructure


class IdempotencyDynamoDBStack(BaseInfrastructure):
    def create_resources(self):
        table = self._create_dynamodb_table()

        env_vars = {"IdempotencyTable": table.table_name}
        functions = self.create_lambda_functions(function_props={"environment": env_vars})

        table.grant_read_write_data(functions["TtlCacheExpirationHandler"])
        table.grant_read_write_data(functions["TtlCacheTimeoutHandler"])
        table.grant_read_write_data(functions["ParallelExecutionHandler"])
        table.grant_read_write_data(functions["FunctionThreadSafetyHandler"])
        table.grant_read_write_data(functions["OptionalIdempotencyKeyHandler"])

    def _create_dynamodb_table(self) -> Table:
        table = dynamodb.Table(
            self.stack,
            "Idempotency",
            removal_policy=RemovalPolicy.DESTROY,
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            time_to_live_attribute="expiration",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        CfnOutput(self.stack, "DynamoDBTable", value=table.table_name)

        return table
