#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.powertools_cdk_stack import PowertoolsStack

app = cdk.App()

# Get environment from context or default to dev
environment = app.node.try_get_context("environment") or "dev"

# Create stack for the specified environment
PowertoolsStack(
    app,
    f"PowertoolsStack-{environment}",
    environment=environment,
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1",
    ),
)

app.synth()
