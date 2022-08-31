from pathlib import Path

from aws_cdk import aws_ec2, aws_ssm
from aws_cdk import aws_elasticloadbalancingv2 as elbv2

from tests.e2e.utils.data_builder import build_service_name
from tests.e2e.utils.infrastructure import BaseInfrastructure


class TracerStack(BaseInfrastructure):
    # Maintenance: Tracer doesn't support dynamic service injection (tracer.py L310)
    # we could move after handler response or adopt env vars usage in e2e tests
    SERVICE_NAME: str = build_service_name()
    FEATURE_NAME = "tracer"

    def __init__(self, handlers_dir: Path, feature_name: str = FEATURE_NAME, layer_arn: str = "") -> None:
        super().__init__(feature_name, handlers_dir, layer_arn)

    def create_resources(self) -> None:
        # NOTE: Commented out Lambda fns as we don't need them now
        # env_vars = {"POWERTOOLS_SERVICE_NAME": self.SERVICE_NAME}
        # self.create_lambda_functions(function_props={"environment": env_vars})

        # NOTE: Test VPC can be looked up
        vpc = aws_ec2.Vpc.from_lookup(
            self.stack,
            "VPC",
            is_default=True,
            region="eu-west-1"
            # vpc_id="vpc-4d79432b",  # NOTE: hardcode didn't work either
        )

        # NOTE: Same issue with any other lookup.
        # # string_value = aws_ssm.StringParameter.from_string_parameter_attributes(
        # #     self.stack, "MyValue", parameter_name="/db/proxy_arn"
        # # ).string_value

        alb = elbv2.ApplicationLoadBalancer(self.stack, "pqp", vpc=vpc, internet_facing=True)
        self.add_cfn_output(name="ALB", value=alb.load_balancer_dns_name, arn=alb.load_balancer_arn)
