from aws_cdk import (
    Stack,
    aws_lambda,
    aws_sam
)
from constructs import Construct

POWERTOOLS_BASE_NAME = 'AWSLambdaPowertools'
# Find latest from github.com/aws-powertools/powertools-lambda-python/releases
POWERTOOLS_VER = '2.37.0'
POWERTOOLS_ARN = 'arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer'

class SampleApp(Stack):

    def __init__(self, scope: Construct, id_: str) -> None:
        super().__init__(scope, id_)

        # Launches SAR App as CloudFormation nested stack and return Lambda Layer
        powertools_app = aws_sam.CfnApplication(self,
            f'{POWERTOOLS_BASE_NAME}Application',
            location={
                'applicationId': POWERTOOLS_ARN,
                'semanticVersion': POWERTOOLS_VER
            },
        )

        powertools_layer_arn = powertools_app.get_att("Outputs.LayerVersionArn").to_string()
        powertools_layer_version = aws_lambda.LayerVersion.from_layer_version_arn(self, f'{POWERTOOLS_BASE_NAME}', powertools_layer_arn)

        aws_lambda.Function(self,
            'sample-app-lambda',
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            function_name='sample-lambda',
            code=aws_lambda.Code.from_asset('lambda'),
            handler='hello.handler',
            layers=[powertools_layer_version]
        )