from aws_lambda_powertools.utilities import parameters

dynamodb_provider = parameters.DynamoDBProvider(
    table_name="my-table",
    key_attr="MyKeyAttr",
    sort_attr="MySortAttr",
    value_attr="MyvalueAttr",
)


def handler(event, context):
    value = dynamodb_provider.get("my-parameter")
