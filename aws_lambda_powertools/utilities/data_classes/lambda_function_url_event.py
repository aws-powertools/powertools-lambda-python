from aws_lambda_powertools.utilities.data_classes.api_gateway_proxy_event import APIGatewayProxyEventV2


class LambdaFunctionUrlEvent(APIGatewayProxyEventV2):
    """AWS Lambda Function URL event

    Notes:
    -----
    For now, this seems to follow the exact same payload as HTTP APIs Payload Format Version 2.0.
    Certain keys in this payload format don't make sense for function urls (e.g: `routeKey`, `stage`).
    These keys will have default values that come on the payload, but they are not useful since they can't be changed.

    Documentation:
    - https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html
    - https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html#urls-payloads
    """

    pass
