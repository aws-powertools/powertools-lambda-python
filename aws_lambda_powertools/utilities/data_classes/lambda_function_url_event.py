from aws_lambda_powertools.utilities.data_classes.api_gateway_proxy_event import APIGatewayProxyEventV2


class LambdaFunctionUrlEvent(APIGatewayProxyEventV2):
    """AWS Lambda Function URL event

    Notes:
    -----
    For now, this seems to follow the exact payload as HTTP APIs Payload Format Version 2.0.
    Certain keys in this payload format don't make sense for function urls (e.g: `routeKey`).
    These keys will always be null.

    Documentation:
    - https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html#urls-payloads
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html

    """

    pass
