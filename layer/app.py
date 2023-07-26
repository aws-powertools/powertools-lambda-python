#!/usr/bin/env python3

import aws_cdk as cdk

from layer.canary_stack import CanaryStack
from layer.layer_stack import LayerStack
from aws_cdk.aws_lambda import Architecture

app = cdk.App()

POWERTOOLS_VERSION: str = app.node.try_get_context("version")
REGION_HAS_ARM64_SUPPORT: str = app.node.try_get_context("HasARM64Support")
SSM_PARAM_LAYER_ARN: str = "/layers/powertools-layer-v2-arn"
SSM_PARAM_LAYER_ARM64_ARN: str = "/layers/powertools-layer-v2-arm64-arn"

if not POWERTOOLS_VERSION:
    raise ValueError(
        "Please set the version for Powertools for AWS Lambda (Python) by passing the '--context version=<version>' parameter to the CDK "
        "synth step."
    )


LayerStack(
    app,
    "LayerV2Stack",
    powertools_version=POWERTOOLS_VERSION,
    ssm_parameter_layer_arn=SSM_PARAM_LAYER_ARN,
    architecture=Architecture.X86_64
)

if REGION_HAS_ARM64_SUPPORT and REGION_HAS_ARM64_SUPPORT.lower() == "true":
    LayerStack(
        app,
        "LayerV2ARM64Stack",
        powertools_version=POWERTOOLS_VERSION,
        ssm_parameter_layer_arn=SSM_PARAM_LAYER_ARM64_ARN,
        architecture=Architecture.ARM_64
    )

CanaryStack(
    app,
    "CanaryV2Stack",
    powertools_version=POWERTOOLS_VERSION,
    ssm_paramter_layer_arn=SSM_PARAM_LAYER_ARN,
    ssm_parameter_layer_arm64_arn=SSM_PARAM_LAYER_ARM64_ARN,
)

app.synth()
