from typing import Any

from aws_cdk import CfnOutput, RemovalPolicy
from aws_cdk import aws_dynamodb as dynamodb

from tests.e2e.utils.infrastructure import BaseInfrastructure


class IdempotencyDynamoDBStack(BaseInfrastructure):
    def create_resources(self):
        functions = self.create_lambda_functions()
        self._create_dynamodb_table(function=functions)

    def _create_dynamodb_table(self, function: Any):
        table = dynamodb.Table(
            self.stack,
            "Idempotency",
            table_name="IdempotencyTable",
            removal_policy=RemovalPolicy.DESTROY,
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            time_to_live_attribute="expiration",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        table.grant_read_write_data(function["TtlCacheExpirationHandler"])
        table.grant_read_write_data(function["TtlCacheTimeoutHandler"])
        table.grant_read_write_data(function["ParallelExecutionHandler"])

        CfnOutput(self.stack, "DynamoDBTable", value=table.table_name)
