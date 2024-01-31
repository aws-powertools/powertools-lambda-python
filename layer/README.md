<!-- markdownlint-disable MD041 MD043-->
# CDK Powertools for AWS Lambda (Python) layer

This is a CDK project to build and deploy Powertools for AWS Lambda (Python) [Lambda layer](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-concepts.html#gettingstarted-concepts-layer) to multiple commercial regions.

## Build the layer

To build the layer construct you need to provide the Powertools for AWS Lambda (Python) version that is [available in PyPi](https://pypi.org/project/aws-lambda-powertools/).
You can pass it as a context variable when running `synth` or `deploy`,

```shell
cdk synth --context version=1.25.1
```

## Canary stack

We use a canary stack to verify that the deployment is successful and we can use the layer by adding it to a newly created Lambda function.
The canary is deployed after the layer construct. Because the layer ARN is created during the deploy we need to pass this information async via SSM parameter.
To achieve that we use SSM parameter store to pass the layer ARN to the canary.
The layer stack writes the layer ARN after the deployment as SSM parameter and the canary stacks reads this information and adds the layer to the function.

## Version tracking

AWS Lambda versions Lambda layers by incrementing a number at the end of the ARN.
This makes it challenging to know which Powertools for AWS Lambda (Python) version a layer contains.
For better tracking of the ARNs and the corresponding version we need to keep track which Powertools for AWS Lambda (Python) version was deployed to which layer.
To achieve that we created two components. First, we created a version tracking app which receives events via EventBridge. Second, after a successful canary deployment we send the layer ARN, Powertools for AWS Lambda (Python) version, and the region to this EventBridge.
