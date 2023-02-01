from typing import Dict, Optional

from aws_cdk import CfnOutput
from aws_cdk import aws_apigateway as apigwv1
from aws_cdk import aws_apigatewayv2_alpha as apigwv2
from aws_cdk import aws_apigatewayv2_authorizers_alpha as apigwv2authorizers
from aws_cdk import aws_apigatewayv2_integrations_alpha as apigwv2integrations
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_elasticloadbalancingv2_targets as targets
from aws_cdk.aws_lambda import Function, FunctionUrlAuthType

from tests.e2e.utils.infrastructure import BaseInfrastructure


class EventHandlerStack(BaseInfrastructure):
    def create_resources(self):
        functions = self.create_lambda_functions()

        self._create_alb(function=functions["AlbHandler"])
        self._create_api_gateway_rest(function=functions["ApiGatewayRestHandler"])
        self._create_api_gateway_http(function=functions["ApiGatewayHttpHandler"])
        self._create_lambda_function_url(function=functions["LambdaFunctionUrlHandler"])

    def _create_alb(self, function: Function):
        vpc = ec2.Vpc.from_lookup(
            self.stack,
            "VPC",
            is_default=True,
            region=self.region,
        )

        alb = elbv2.ApplicationLoadBalancer(self.stack, "ALB", vpc=vpc, internet_facing=True)
        CfnOutput(self.stack, "ALBDnsName", value=alb.load_balancer_dns_name)

        self._create_alb_listener(alb=alb, name="Basic", port=80, function=function)
        self._create_alb_listener(
            alb=alb,
            name="MultiValueHeader",
            port=8080,
            function=function,
            attributes={"lambda.multi_value_headers.enabled": "true"},
        )

    def _create_alb_listener(
        self,
        alb: elbv2.ApplicationLoadBalancer,
        name: str,
        port: int,
        function: Function,
        attributes: Optional[Dict[str, str]] = None,
    ):
        listener = alb.add_listener(name, port=port, protocol=elbv2.ApplicationProtocol.HTTP)
        target = listener.add_targets(f"ALB{name}Target", targets=[targets.LambdaTarget(function)])
        if attributes is not None:
            for key, value in attributes.items():
                target.set_attribute(key, value)
        CfnOutput(self.stack, f"ALB{name}ListenerPort", value=str(port))

    def _create_api_gateway_http(self, function: Function):
        apigw = apigwv2.HttpApi(
            self.stack,
            "APIGatewayHTTP",
            create_default_stage=True,
            default_authorizer=apigwv2authorizers.HttpIamAuthorizer(),
        )
        apigw.add_routes(
            path="/todos",
            methods=[apigwv2.HttpMethod.POST],
            integration=apigwv2integrations.HttpLambdaIntegration("TodosIntegration", function),
        )

        CfnOutput(self.stack, "APIGatewayHTTPUrl", value=(apigw.url or ""))

    def _create_api_gateway_rest(self, function: Function):
        apigw = apigwv1.RestApi(self.stack, "APIGatewayRest", deploy_options=apigwv1.StageOptions(stage_name="dev"))

        todos = apigw.root.add_resource("todos")
        todos.add_method("POST", apigwv1.LambdaIntegration(function, proxy=True))

        CfnOutput(self.stack, "APIGatewayRestUrl", value=apigw.url)

    def _create_lambda_function_url(self, function: Function):
        # Maintenance: move auth to IAM when we create sigv4 builders
        function_url = function.add_function_url(auth_type=FunctionUrlAuthType.AWS_IAM)
        CfnOutput(self.stack, "LambdaFunctionUrl", value=function_url.url)
