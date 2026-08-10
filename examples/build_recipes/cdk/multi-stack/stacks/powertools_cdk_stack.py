from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_apigateway as apigateway,
)
from aws_cdk import (
    aws_dynamodb as dynamodb,
)
from aws_cdk import (
    aws_lambda as _lambda,
)
from aws_cdk import (
    aws_lambda_event_sources as lambda_event_sources,
)
from aws_cdk import (
    aws_sqs as sqs,
)
from constructs import Construct


class PowertoolsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str = "dev", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.deploy_environment = environment

        # Shared Powertools Layer (using public layer)
        self.powertools_layer = self._create_powertools_layer()

        # DynamoDB Table
        self.table = self._create_dynamodb_table()

        # SQS Queue
        self.queue = self._create_sqs_queue()

        # Lambda Functions
        self.api_function = self._create_api_function()
        self.worker_function = self._create_worker_function()

        # API Gateway
        self.api = self._create_api_gateway()

    def _create_powertools_layer(self) -> _lambda.ILayerVersion:
        return _lambda.LayerVersion.from_layer_version_arn(
            self,
            "PowertoolsLayer",
            layer_version_arn="arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-x86_64:37",
        )

    def _create_dynamodb_table(self) -> dynamodb.Table:
        return dynamodb.Table(
            self,
            "DataTable",
            table_name=f"powertools-{self.deploy_environment}-data",
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if self.deploy_environment != "prod" else RemovalPolicy.RETAIN,
        )

    def _create_sqs_queue(self) -> sqs.Queue:
        return sqs.Queue(
            self,
            "WorkerQueue",
            queue_name=f"powertools-{self.deploy_environment}-worker",
            visibility_timeout=Duration.seconds(180),
        )

    def _create_api_function(self) -> _lambda.Function:
        function = _lambda.Function(
            self,
            "ApiFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="app.lambda_handler",
            code=_lambda.Code.from_asset("src/app"),
            layers=[self.powertools_layer],
            timeout=Duration.seconds(30),
            memory_size=512 if self.deploy_environment == "prod" else 256,
            environment={
                "ENVIRONMENT": self.deploy_environment,
                "POWERTOOLS_SERVICE_NAME": f"app-{self.deploy_environment}",
                "POWERTOOLS_METRICS_NAMESPACE": f"MyApp/{self.deploy_environment}",
                "POWERTOOLS_LOG_LEVEL": "INFO" if self.deploy_environment == "prod" else "DEBUG",
                "TABLE_NAME": self.table.table_name,
                "QUEUE_URL": self.queue.queue_url,
            },
        )

        # Grant permissions
        self.table.grant_read_write_data(function)
        self.queue.grant_send_messages(function)

        return function

    def _create_worker_function(self) -> _lambda.Function:
        function = _lambda.Function(
            self,
            "WorkerFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="worker.lambda_handler",
            code=_lambda.Code.from_asset("src/worker"),
            layers=[self.powertools_layer],
            timeout=Duration.seconds(120),
            memory_size=1024 if self.deploy_environment == "prod" else 512,
            environment={
                "ENVIRONMENT": self.deploy_environment,
                "POWERTOOLS_SERVICE_NAME": f"worker-{self.deploy_environment}",
                "POWERTOOLS_METRICS_NAMESPACE": f"MyApp/{self.deploy_environment}",
                "POWERTOOLS_LOG_LEVEL": "INFO" if self.deploy_environment == "prod" else "DEBUG",
                "TABLE_NAME": self.table.table_name,
            },
        )

        # Add SQS event source with partial failure support
        function.add_event_source(
            lambda_event_sources.SqsEventSource(
                self.queue,
                batch_size=10,
                report_batch_item_failures=True,
            ),
        )

        # Grant permissions
        self.table.grant_read_write_data(function)

        return function

    def _create_api_gateway(self) -> apigateway.RestApi:
        api = apigateway.RestApi(
            self,
            "ApiGateway",
            rest_api_name=f"Powertools API - {self.deploy_environment}",
            description=f"API for {self.deploy_environment} environment",
        )

        integration = apigateway.LambdaIntegration(self.api_function)
        api.root.add_proxy(
            default_integration=integration,
            any_method=True,
        )

        return api
