import io
import os
import zipfile
from pathlib import Path

import boto3
import yaml
from aws_cdk import App, CfnOutput, RemovalPolicy, Stack, aws_lambda_python_alpha, aws_logs
from aws_cdk.aws_lambda import Code, Function, Runtime, Tracing


class Infrastructure:
    def __init__(self, stack_name: str, handlers_dir: str, config: dict, environment_variables: dict) -> None:
        session = boto3.Session(profile_name="aws-mploski-root")
        self.s3_client = session.client("s3")
        self.lambda_client = session.client("lambda")
        self.cf_client = session.client("cloudformation")
        self.s3_resource = session.resource("s3")
        self.account_id = session.client("sts").get_caller_identity()["Account"]
        self.region = boto3.Session().region_name
        self.stack_name = stack_name
        self.handlers_dir = handlers_dir
        self.config = config
        self.environment_variables = environment_variables

    def deploy(self) -> dict:

        handlers = self._find_files(directory=self.handlers_dir, only_py=True)

        template, asset_root_dir, artifact = self._prepare_stack(
            handlers=handlers,
            handlers_dir=self.handlers_dir,
            stack_name=self.stack_name,
            environment_variables=self.environment_variables,
            **self.config,
        )
        self._upload_assets(template, asset_root_dir)

        response = self._deploy_stack(self.stack_name, template)

        return self._transform_output(response["Stacks"][0]["Outputs"])

    def delete(self):
        self.cf_client.delete_stack(StackName=self.stack_name)

    def _find_files(self, directory, only_py=False) -> list:
        file_paths = []
        for root, _, files in os.walk(directory):
            for filename in files:
                if only_py:
                    if filename.endswith(".py"):
                        file_paths.append(os.path.join(root, filename))
                else:
                    file_paths.append(os.path.join(root, filename))
        return file_paths

    # Create CDK cloud assembly code
    def _prepare_stack(self, handlers, handlers_dir, stack_name, environment_variables, **config):
        integration_test_app = App()
        stack = Stack(integration_test_app, stack_name)
        powertools_layer = aws_lambda_python_alpha.PythonLayerVersion(
            stack,
            "aws-lambda-powertools",
            layer_version_name="aws-lambda-powertools",
            entry=".",
            compatible_runtimes=[Runtime.PYTHON_3_9],
        )
        code = Code.from_asset(handlers_dir)

        for filename_path in handlers:
            filename = Path(filename_path).stem
            function_python = Function(
                stack,
                f"{filename}-lambda",
                runtime=Runtime.PYTHON_3_9,
                code=code,
                handler=f"{filename}.lambda_handler",
                layers=[powertools_layer],
                environment=environment_variables,
                tracing=Tracing.ACTIVE if config.get("tracing") == "ACTIVE" else Tracing.DISABLED,
            )

            aws_logs.LogGroup(
                stack,
                f"{filename}-lg",
                log_group_name=f"/aws/lambda/{function_python.function_name}",
                retention=aws_logs.RetentionDays.ONE_DAY,
                removal_policy=RemovalPolicy.DESTROY,
            )
            CfnOutput(stack, f"{filename}_arn", value=function_python.function_arn)
        return (
            integration_test_app.synth().get_stack_by_name(stack_name).template,
            integration_test_app.synth().directory,
            integration_test_app.synth().artifacts,
        )

    def _upload_assets(self, template, asset_root_dir):

        assets = self._find_assets(template, self.account_id, self.region)

        for s3_key, bucket in assets.items():
            s3_bucket = self.s3_resource.Bucket(bucket)
            if bool(list(s3_bucket.objects.filter(Prefix=s3_key))):
                print("object exists, skipping")
                continue

            buf = io.BytesIO()
            asset_dir = f"{asset_root_dir}/asset.{Path(s3_key).with_suffix('')}"
            os.chdir(asset_dir)
            files = self._find_files(directory=".")
            with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for file in files:
                    zf.write(os.path.join(file))
            buf.seek(0)
            self.s3_client.upload_fileobj(Fileobj=buf, Bucket=bucket, Key=s3_key)

    def _deploy_stack(self, stack_name, template):
        response = self.cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=yaml.dump(template),
            TimeoutInMinutes=10,
            OnFailure="DO_NOTHING",
            Capabilities=["CAPABILITY_IAM"],
        )
        waiter = self.cf_client.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name, WaiterConfig={"Delay": 2, "MaxAttempts": 50})
        response = self.cf_client.describe_stacks(StackName=stack_name)
        return response

    def _find_assets(self, template, account_id, region):
        assets = {}
        for name, resource in template["Resources"].items():
            bucket = None
            S3Key = None

            if resource["Properties"].get("Code"):
                bucket = resource["Properties"]["Code"]["S3Bucket"]
                S3Key = resource["Properties"]["Code"]["S3Key"]
            elif resource["Properties"].get("Content"):
                bucket = resource["Properties"]["Content"]["S3Bucket"]
                S3Key = resource["Properties"]["Content"]["S3Key"]
            if S3Key and bucket:
                assets[S3Key] = (
                    bucket["Fn::Sub"].replace("${AWS::AccountId}", account_id).replace("${AWS::Region}", region)
                )
        return assets

    def _transform_output(self, outputs):
        return {output["OutputKey"]: output["OutputValue"] for output in outputs if output["OutputKey"]}
