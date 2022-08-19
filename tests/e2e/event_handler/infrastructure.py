from pathlib import Path

from aws_cdk import CfnOutput
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_elasticloadbalancingv2_targets as targets

from tests.e2e.utils.infrastructure import BaseInfrastructureV2


class EventHandlerStack(BaseInfrastructureV2):
    def __init__(self, handlers_dir: Path, feature_name: str = "event-handlers") -> None:
        super().__init__(feature_name, handlers_dir)

    def create_resources(self):
        functions = self.create_lambda_functions()
        api_gateway_http_handler_function = functions["AlbHandler"]

        vpc = ec2.Vpc(self.stack, "EventHandlerVPC", max_azs=2)

        alb = elbv2.ApplicationLoadBalancer(self.stack, "ALB", vpc=vpc, internet_facing=True)
        listener = alb.add_listener("HTTPListener", port=80)
        listener.add_targets("HTTPListenerTarget", targets=[targets.LambdaTarget(api_gateway_http_handler_function)])

        CfnOutput(self.stack, "ALBDnsName", value=alb.load_balancer_dns_name)
