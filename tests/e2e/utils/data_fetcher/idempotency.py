import boto3
from retry import retry


@retry(ValueError, delay=2, jitter=1.5, tries=10)
def get_ddb_idempotency_record(
    function_name: str,
    table_name: str,
) -> int:
    """_summary_

    Parameters
    ----------
    function_name : str
        Name of Lambda function to fetch dynamodb record
    table_name : str
            Name of DynamoDB table

    Returns
    -------
    int
        Count of records found

    Raises
    ------
    ValueError
        When no record is found within retry window
    """
    ddb_client = boto3.resource("dynamodb")
    table = ddb_client.Table(table_name)
    ret = table.scan(
        FilterExpression="contains (id, :functionName)",
        ExpressionAttributeValues={":functionName": f"{function_name}#"},
    )

    if not ret["Items"]:
        raise ValueError("Empty response from DynamoDB Repeating...")

    return ret["Count"]
