#!/usr/bin/env python3

import aws_cdk as cdk

from layer.canary_stack import CanaryStack
from layer.layer_stack import LayerStack

app = cdk.App()

POWERTOOLS_VERSION: str = app.node.try_get_context("version")
PYTHON_VERSION: str = app.node.try_get_context("pythonVersion")
PYTHON_VERSION_NORMALIZED = PYTHON_VERSION.replace(".", "")
SSM_PARAM_LAYER_ARN: str = f"/layers/powertools-layer-v3-{PYTHON_VERSION_NORMALIZED}-x86-arn"
SSM_PARAM_LAYER_ARM64_ARN: str = f"/layers/powertools-layer-v3-{PYTHON_VERSION_NORMALIZED}-arm64-arn"

# Validate context variables
if not PYTHON_VERSION:
    raise ValueError(
        "Please set the version for Python by passing the '--context pythonVersion=<version>' parameter to the CDK "
        "synth step.",
    )

if not POWERTOOLS_VERSION:
    raise ValueError(
        "Please set the version for Powertools by passing the '--context version=<version>' parameter to the CDK "
        "synth step.",
    )

LayerStack(
    app,
    f"LayerV3Stack-{PYTHON_VERSION_NORMALIZED}",
    powertools_version=POWERTOOLS_VERSION,
    python_version=PYTHON_VERSION,
    ssm_parameter_layer_arn=SSM_PARAM_LAYER_ARN,
    ssm_parameter_layer_arm64_arn=SSM_PARAM_LAYER_ARM64_ARN,
)

CanaryStack(
    app,
    f"CanaryV3Stack-{PYTHON_VERSION_NORMALIZED}",
    powertools_version=POWERTOOLS_VERSION,
    python_version=PYTHON_VERSION,
    ssm_paramter_layer_arn=SSM_PARAM_LAYER_ARN,
    ssm_parameter_layer_arm64_arn=SSM_PARAM_LAYER_ARM64_ARN,
)

app.synth()
