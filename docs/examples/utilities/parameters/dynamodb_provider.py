from aws_lambda_powertools.utilities import parameters

dynamodb_provider = parameters.DynamoDBProvider(table_name="my-table")


def handler(event, context):
    # Retrieve a value from DynamoDB
    value = dynamodb_provider.get("my-parameter")
