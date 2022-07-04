#!/usr/bin/env python3

import aws_cdk as cdk

from layer.canary_stack import CanaryStack
from layer.layer_stack import LayerStack

app = cdk.App()

POWERTOOLS_VERSION: str = app.node.try_get_context("version")
SSM_PARAM_LAYER_ARN: str = "/layers/powertools-layer-arn"

VERSION_TRACKING_EVENT_BUS_ARN: str = "arn:aws:events:eu-central-1:027876851704:event-bus/VersionTrackingEventBus"

if not POWERTOOLS_VERSION:
    raise ValueError(
        "Please set the version for Powertools by passing the '--context=version:<version>' parameter to the CDK "
        "synth step."
    )

LayerStack(app, "LayerStack", powertools_version=POWERTOOLS_VERSION, ssm_paramter_layer_arn=SSM_PARAM_LAYER_ARN)

CanaryStack(
    app,
    "CanaryStack",
    powertools_version=POWERTOOLS_VERSION,
    ssm_paramter_layer_arn=SSM_PARAM_LAYER_ARN,
    version_tracking_event_bus_arn=VERSION_TRACKING_EVENT_BUS_ARN,
)

app.synth()
