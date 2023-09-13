import aws_cdk.aws_kms as kms
from aws_cdk import CfnOutput, Duration
from aws_cdk import aws_iam as iam

from tests.e2e.utils.infrastructure import BaseInfrastructure


class DataMaskingStack(BaseInfrastructure):
    def create_resources(self):
        functions = self.create_lambda_functions(function_props={"timeout": Duration.seconds(10)})

        key1 = kms.Key(self.stack, "MyKMSKey1", description="My KMS Key1")
        CfnOutput(self.stack, "KMSKey1Arn", value=key1.key_arn, description="ARN of the created KMS Key1")

        key2 = kms.Key(self.stack, "MyKMSKey2", description="My KMS Key2")
        CfnOutput(self.stack, "KMSKey2Arn", value=key2.key_arn, description="ARN of the created KMS Key2")

        functions["BasicHandler"].add_to_role_policy(
            iam.PolicyStatement(effect=iam.Effect.ALLOW, actions=["kms:*"], resources=[key1.key_arn, key2.key_arn]),
        )
