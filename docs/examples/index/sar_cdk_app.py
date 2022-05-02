from aws_cdk import aws_lambda
from aws_cdk import aws_sam as sam
from aws_cdk import core

POWERTOOLS_BASE_NAME = "AWSLambdaPowertools"
# Find latest from github.com/awslabs/aws-lambda-powertools-python/releases
POWERTOOLS_VER = "1.25.10"
POWERTOOLS_ARN = "arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer"


class SampleApp(core.Construct):
    def __init__(self, scope: core.Construct, id_: str) -> None:
        super().__init__(scope, id_)

        # Launches SAR App as CloudFormation nested stack and return Lambda Layer
        powertools_app = sam.CfnApplication(
            self,
            f"{POWERTOOLS_BASE_NAME}Application",
            location={"applicationId": POWERTOOLS_ARN, "semanticVersion": POWERTOOLS_VER},
        )

        powertools_layer_arn = powertools_app.get_att("Outputs.LayerVersionArn").to_string()
        powertools_layer_version = aws_lambda.LayerVersion.from_layer_version_arn(
            self, f"{POWERTOOLS_BASE_NAME}", powertools_layer_arn
        )

        aws_lambda.Function(
            self,
            "sample-app-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            function_name="sample-lambda",
            code=aws_lambda.Code.asset("./src"),
            handler="app.handler",
            layers=[powertools_layer_version],
        )
