from aws_cdk import RemovalPolicy
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from constructs import Construct


class IdempotencyConstruct(Construct):
    def __init__(self, scope: Construct, id_: str, lambda_role: iam.Role) -> None:
        super().__init__(scope, id_)
        self.idempotency_table = dynamodb.Table(
            self,
            "IdempotencyTable",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="expiration",
            point_in_time_recovery=True,
        )
        self.idempotency_table.grant(lambda_role, "dynamodb:PutItem")
        self.idempotency_table.grant(lambda_role, "dynamodb:GetItem")
        self.idempotency_table.grant(lambda_role, "dynamodb:UpdateItem")
        self.idempotency_table.grant(lambda_role, "dynamodb:DeleteItem")
