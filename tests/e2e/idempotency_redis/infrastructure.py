import time
from typing import Tuple

from aws_cdk import aws_ec2 as ec2
from aws_cdk.aws_ec2 import (
    SecurityGroup,
    SubnetType,
    Vpc,
)
from aws_cdk.aws_elasticache import (
    CfnServerlessCache,
)

from tests.e2e.utils.data_builder import build_random_value
from tests.e2e.utils.infrastructure import BaseInfrastructure


class IdempotencyRedisServerlessStack(BaseInfrastructure):
    def create_resources(self) -> None:
        service_name = build_random_value(10)

        vpc_stack: Vpc = self._create_vpc(service_name, "172.150.0.0/16")
        security_groups: Tuple = self._create_security_groups(vpc_stack)
        redis_cluster: CfnServerlessCache = self._create_redis_cache(service_name, vpc_stack, security_groups[0])

        env_vars = {"RedisEndpoint": f"{str(redis_cluster.attr_endpoint_address)}"}

        self.create_lambda_functions(
            function_props={
                "environment": env_vars,
                "vpc": vpc_stack,
                "security_groups": [security_groups[1]],
            },
        )

    def _create_vpc(self, service_name: str, cidr: str) -> Vpc:
        vpc_stack: Vpc = Vpc(
            self.stack,
            "VPC-ServerlessCache",
            nat_gateways=1,
            vpc_name=f"VPC-ServerlessCache-{service_name}",
            ip_addresses=ec2.IpAddresses.cidr(cidr),
            subnet_configuration=[
                ec2.SubnetConfiguration(name="public", subnet_type=SubnetType.PUBLIC, cidr_mask=24),
                ec2.SubnetConfiguration(name="private", subnet_type=SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24),
            ],
            max_azs=2,
        )

        return vpc_stack

    def _create_security_groups(self, vpc_stack: Vpc) -> Tuple[SecurityGroup, SecurityGroup]:
        # Create a security group for the ElastiCache cluster
        cache_security_group: SecurityGroup = SecurityGroup(self.stack, "ElastiCacheSecurityGroup", vpc=vpc_stack)
        cache_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc_stack.vpc_cidr_block),
            connection=ec2.Port.tcp(6379),
            description="Allow inbound traffic from VPC",
        )

        lambda_security_group = SecurityGroup(
            self.stack,
            "LambdaSecurityGroup",
            vpc=vpc_stack,
            allow_all_ipv6_outbound=True,
            allow_all_outbound=True,
        )

        return cache_security_group, lambda_security_group

    def _create_redis_cache(
        self,
        service_name: str,
        vpc_stack: Vpc,
        cache_security_group: SecurityGroup,
    ) -> CfnServerlessCache:
        cache_cluster = CfnServerlessCache(
            self.stack,
            "ElastiCacheCluster",
            engine="redis",
            security_group_ids=[cache_security_group.security_group_id],
            subnet_ids=[subnet.subnet_id for subnet in vpc_stack.private_subnets],
            serverless_cache_name=f"Cache-{service_name}",
        )

        # Just to make sure the Cluster will be ready before the Stack is complete
        while cache_cluster.attr_status == "CREATING":
            print("Waiting for ElastiCache serverless to be created...")
            time.sleep(5)

        return cache_cluster
