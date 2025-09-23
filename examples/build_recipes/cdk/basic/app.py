#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import (
    Duration,
    Stack,
)
from aws_cdk import (
    aws_apigateway as apigateway,
)
from aws_cdk import (
    aws_lambda as _lambda,
)
from aws_cdk import (
    aws_logs as logs,
)
from constructs import Construct


class PowertoolsLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Use public Powertools layer
        powertools_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "PowertoolsLayer",
            layer_version_arn="arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-x86_64:23",
        )

        # Lambda Function
        api_function = _lambda.Function(
            self,
            "ApiFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("src"),
            layers=[powertools_layer],
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "POWERTOOLS_SERVICE_NAME": "api-service",
                "POWERTOOLS_METRICS_NAMESPACE": "MyApp",
                "POWERTOOLS_LOG_LEVEL": "INFO",
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # API Gateway
        api = apigateway.RestApi(
            self,
            "ApiGateway",
            rest_api_name="Powertools API",
            description="API powered by Lambda with Powertools",
        )

        # API Integration
        integration = apigateway.LambdaIntegration(api_function)
        api.root.add_proxy(
            default_integration=integration,
            any_method=True,
        )

        # Outputs
        cdk.CfnOutput(
            self,
            "ApiUrl",
            value=api.url,
            description="API Gateway URL",
        )


app = cdk.App()
PowertoolsLambdaStack(app, "PowertoolsLambdaStack")
app.synth()
