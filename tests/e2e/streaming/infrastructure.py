from pathlib import Path

from aws_cdk import CfnOutput, RemovalPolicy
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy

from tests.e2e.utils.infrastructure import BaseInfrastructure


class StreamingStack(BaseInfrastructure):
    def create_resources(self):
        functions = self.create_lambda_functions()

        regular_bucket = s3.Bucket(
            self.stack,
            "S3Bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )
        self.create_s3_deployment(regular_bucket)

        for function in functions.values():
            regular_bucket.grant_read(function)

        CfnOutput(self.stack, "RegularBucket", value=regular_bucket.bucket_name)

        versioned_bucket = s3.Bucket(
            self.stack,
            "S3VersionedBucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )
        self.create_s3_deployment(versioned_bucket)

        for function in functions.values():
            versioned_bucket.grant_read(function)

        CfnOutput(self.stack, "VersionedBucket", value=versioned_bucket.bucket_name)

    def create_s3_deployment(self, bucket: s3.IBucket):
        current_dir = Path(__file__).parent.resolve()
        sources = [s3deploy.Source.asset(str(current_dir / "assets"))]

        s3deploy.BucketDeployment(
            self.stack,
            f"Deployment{bucket.node.id}",
            sources=sources,
            destination_bucket=bucket,
        )
