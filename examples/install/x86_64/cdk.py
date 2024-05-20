from aws_cdk import (
    Stack,
    aws_lambda,
    Aws
)
from constructs import Construct

class SampleApp(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        powertools_layer = aws_lambda.LayerVersion.from_layer_version_arn(
            self,
            id="lambda-powertools",
            layer_version_arn=f"arn:aws:lambda:{Aws.REGION}:017000801446:layer:AWSLambdaPowertoolsPythonV2:69"
        )
        aws_lambda.Function(self,
            'sample-app-lambda',
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            layers=[powertools_layer],
            code=aws_lambda.Code.from_asset('lambda'),
            handler='hello.handler'
        )
