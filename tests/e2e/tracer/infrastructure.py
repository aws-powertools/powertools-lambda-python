from pathlib import Path

from aws_cdk import aws_ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_ssm

from tests.e2e.utils.data_builder import build_service_name
from tests.e2e.utils.infrastructure import BaseInfrastructure

PWD = Path(__file__).parent


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
            region=self.region,
        )

        aws_ssm.StringParameter(self.stack, "MyParam", string_value="blah", parameter_name="/dummy/cdk/param")

        # NOTE: Tokens work, but `lookup` doesn't due to context being populated by the CLI
        latest_string_token = aws_ssm.StringParameter.value_for_string_parameter(self.stack, "/db/proxy_arn")

        # alb = elbv2.ApplicationLoadBalancer(self.stack, "pqp", vpc=vpc, internet_facing=True)
        # self.add_cfn_output(name="ALB", value=alb.load_balancer_dns_name, arn=alb.load_balancer_arn)
        self.add_cfn_output(name="ProxyArn", value=latest_string_token)
        self.add_cfn_output(name="LookupVPC", value=vpc.vpc_arn)
