"""
Amazon DynamoDB parameter retrieval and caching utility
"""


from typing import Dict, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config

from .base import BaseProvider


class DynamoDBProvider(BaseProvider):
    """
    Amazon DynamoDB Parameter Provider

    Example
    -------
    **Retrieves a parameter value from a DynamoDB table**

    In this example, the DynamoDB table uses `id` as hash key and stores the value in the `value`
    attribute.

        >>> from aws_lambda_powertools.utilities.parameters import DynamoDBProvider
        >>> ddb_provider = DynamoDBProvider("ParametersTable")
        >>>
        >>> ddb_provider.get("my-parameter")

    **Retrieves a parameter value from a DynamoDB table that has custom attribute names**

        >>> from aws_lambda_powertools.utilities.parameters import DynamoDBProvider
        >>> ddb_provider = DynamoDBProvider(
        ...     "ParametersTable",
        ...     key_attr="my-id",
        ...     value_attr="my-value"
        ... )
        >>>
        >>> ddb_provider.get("my-parameter")

    **Retrieves a parameter value from a DynamoDB table in another AWS region**

        >>> from botocore.config import Config
        >>> from aws_lambda_powertools.utilities.parameters import DynamoDBProvider
        >>>
        >>> config = Config(region_name="us-west-1")
        >>> ddb_provider = DynamoDBProvider("ParametersTable", config=config)
        >>>
        >>> ddb_provider.get("my-parameter")

    **Retrieves multiple values from a DynamoDB table**

    In this case, the provider will use a sort key to retrieve multiple values using a query under
    the hood. This expects that the sort key is named `sk`.

        >>> from aws_lambda_powertools.utilities.parameters import DynamoDBProvider
        >>> ddb_provider = DynamoDBProvider("ParametersTable")
        >>>
        >>> ddb_provider.get_multiple("my-parameters")

    **Retrieves multiple values from a DynamoDB table with a custom sort key**

    In this case, the provider will use a sort key to retrieve multiple values using a query under
    the hood.

        >>> from aws_lambda_powertools.utilities.parameters import DynamoDBProvider
        >>> ddb_provider = DynamoDBProvider("ParametersTable")
        >>>
        >>> ddb_provider.get_multiple("my-parameters", sort_attr="my-sort-attr")

    """

    table = None
    key_attr = None
    value_attr = None

    def __init__(
        self, table_name: str, key_attr: str = "id", value_attr: str = "value", config: Optional[Config] = None,
    ):
        """
        Initialize the DynamoDB client
        """

        config = config or Config()
        self.table = boto3.resource("dynamodb", config=config).Table(table_name)

        self.key_attr = key_attr
        self.value_attr = value_attr

        super().__init__()

    def _get(self, name: str, **kwargs) -> str:
        """
        Retrieve a parameter value from Amazon DynamoDB
        """

        return self.table.get_item(Key={self.key_attr: name})["Item"][self.value_attr]

    def _get_multiple(self, path: str, sort_attr: str = "sk", **kwargs) -> Dict[str, str]:
        """
        Retrieve multiple parameter values from Amazon DynamoDB

        Parameters
        ----------
        path: str
            Path to retrieve the parameters
        sort_attr: str
            Name of the DynamoDB table sort key (defaults to 'sk')
        """

        response = self.table.query(KeyConditionExpression=Key(self.key_attr).eq(path))
        items = response.get("Items", [])

        # Keep querying while there are more items matching the partition key
        while "LastEvaluatedKey" in response:
            response = self.table.query(
                KeyConditionExpression=Key(self.key_attr).eq(path), ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        retval = {}
        for item in items:
            retval[item[sort_attr]] = item[self.value_attr]

        return retval
