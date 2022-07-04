#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import {LayerStack} from '../lib/layer-stack';
import {CanaryStack} from "../lib/canary-stack";

const app = new cdk.App();
const POWERTOOLS_VERSION: string = app.node.tryGetContext("version");
const SSM_PARAM_LAYER_ARN: string = "/layers/powertools-layer-arn";

// fixed ARN for event bus notification of version tracking
export const VERSION_TRACKING_EVENT_BUS_ARN = `arn:aws:events:eu-central-1:027876851704:event-bus/VersionTrackingEventBus`;

if (!POWERTOOLS_VERSION) {
    throw new Error("Please set the version for Powertools by passing the '--context=version:<version>' parameter to the CDK synth step.");
} else {
    console.log(`Powertools version set: ${POWERTOOLS_VERSION}`);
}

new LayerStack(app, 'LayerStack', {
    version: POWERTOOLS_VERSION,
    ssmParameterLayerArn: SSM_PARAM_LAYER_ARN
});

new CanaryStack(app, 'CanaryStack', {
    powertoolsVersion: POWERTOOLS_VERSION,
    ssmParameterLayerArn: SSM_PARAM_LAYER_ARN,
    versionTrackerEventBusArn: VERSION_TRACKING_EVENT_BUS_ARN
})
