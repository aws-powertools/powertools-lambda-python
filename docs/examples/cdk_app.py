from aws_cdk import aws_lambda, core


class SampleApp(core.Construct):
    def __init__(self, scope: core.Construct, id_: str, env: core.Environment) -> None:
        super().__init__(scope, id_)

        powertools_layer = aws_lambda.LayerVersion.from_layer_version_arn(
            self,
            id="lambda-powertools",
            layer_version_arn=f"arn:aws:lambda:{env.region}:017000801446:layer:AWSLambdaPowertoolsPython:13",
        )
        aws_lambda.Function(
            self,
            "sample-app-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            layers=[powertools_layer]
            # other props...
        )
