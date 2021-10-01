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

    Parameters
    ----------
    table_name: str
        Name of the DynamoDB table that stores parameters
    key_attr: str, optional
        Hash key for the DynamoDB table (default to 'id')
    sort_attr: str, optional
        Name of the DynamoDB table sort key (defaults to 'sk'), used only for get_multiple
    value_attr: str, optional
        Attribute that contains the values in the DynamoDB table (defaults to 'value')
    endpoint_url: str, optional
        Complete url to reference local DynamoDB instance, e.g. http://localhost:8080
    config: botocore.config.Config, optional
        Botocore configuration to pass during client initialization
    boto3_session : boto3.session.Session, optional
            Boto3 session to use for AWS API communication

    Example
    -------
    **Retrieves a parameter value from a DynamoDB table**

    In this example, the DynamoDB table uses `id` as hash key and stores the value in the `value`
    attribute. The parameter item looks like this:

        { "id": "my-parameters", "value": "Parameter value a" }

        >>> from aws_lambda_powertools.utilities.parameters import DynamoDBProvider
        >>> ddb_provider = DynamoDBProvider("ParametersTable")
        >>>
        >>> value = ddb_provider.get("my-parameter")
        >>>
        >>> print(value)
        My parameter value

    **Retrieves a parameter value from a DynamoDB table that has custom attribute names**

        >>> from aws_lambda_powertools.utilities.parameters import DynamoDBProvider
        >>> ddb_provider = DynamoDBProvider(
        ...     "ParametersTable",
        ...     key_attr="my-id",
        ...     value_attr="my-value"
        ... )
        >>>
        >>> value = ddb_provider.get("my-parameter")
        >>>
        >>> print(value)
        My parameter value

    **Retrieves a parameter value from a DynamoDB table in another AWS region**

        >>> from botocore.config import Config
        >>> from aws_lambda_powertools.utilities.parameters import DynamoDBProvider
        >>>
        >>> config = Config(region_name="us-west-1")
        >>> ddb_provider = DynamoDBProvider("ParametersTable", config=config)
        >>>
        >>> value = ddb_provider.get("my-parameter")
        >>>
        >>> print(value)
        My parameter value

    **Retrieves a parameter value from a DynamoDB table passing options to the SDK call**

        >>> from aws_lambda_powertools.utilities.parameters import DynamoDBProvider
        >>> ddb_provider = DynamoDBProvider("ParametersTable")
        >>>
        >>> value = ddb_provider.get("my-parameter", ConsistentRead=True)
        >>>
        >>> print(value)
        My parameter value

    **Retrieves multiple values from a DynamoDB table**

    In this case, the provider will use a sort key to retrieve multiple values using a query under
    the hood. This expects that the sort key is named `sk`. The DynamoDB table contains three items
    looking like this:

        { "id": "my-parameters", "sk": "a", "value": "Parameter value a" }
        { "id": "my-parameters", "sk": "b", "value": "Parameter value b" }
        { "id": "my-parameters", "sk": "c", "value": "Parameter value c" }

        >>> from aws_lambda_powertools.utilities.parameters import DynamoDBProvider
        >>> ddb_provider = DynamoDBProvider("ParametersTable")
        >>>
        >>> values = ddb_provider.get_multiple("my-parameters")
        >>>
        >>> for key, value in values.items():
        ...     print(key, value)
        a   Parameter value a
        b   Parameter value b
        c   Parameter value c

    **Retrieves multiple values from a DynamoDB table that has custom attribute names**

    In this case, the provider will use a sort key to retrieve multiple values using a query under
    the hood.

        >>> from aws_lambda_powertools.utilities.parameters import DynamoDBProvider
        >>> ddb_provider = DynamoDBProvider(
        ...     "ParametersTable",
        ...     key_attr="my-id",
        ...     sort_attr="my-sort-key",
        ...     value_attr="my-value"
        ... )
        >>>
        >>> values = ddb_provider.get_multiple("my-parameters")
        >>>
        >>> for key, value in values.items():
        ...     print(key, value)
        a   Parameter value a
        b   Parameter value b
        c   Parameter value c

    **Retrieves multiple values from a DynamoDB table passing options to the SDK calls**

        >>> from aws_lambda_powertools.utilities.parameters import DynamoDBProvider
        >>> ddb_provider = DynamoDBProvider("ParametersTable")
        >>>
        >>> values = ddb_provider.get_multiple("my-parameters", ConsistentRead=True)
        >>>
        >>> for key, value in values.items():
        ...     print(key, value)
        a   Parameter value a
        b   Parameter value b
        c   Parameter value c
    """

    def __init__(
        self,
        table_name: str,
        key_attr: str = "id",
        sort_attr: str = "sk",
        value_attr: str = "value",
        endpoint_url: Optional[str] = None,
        config: Optional[Config] = None,
        boto3_session: Optional[boto3.session.Session] = None,
    ):
        """
        Initialize the DynamoDB client
        """

        config = config or Config()
        session = boto3_session or boto3.session.Session()

        self.table = session.resource("dynamodb", endpoint_url=endpoint_url, config=config).Table(table_name)

        self.key_attr = key_attr
        self.sort_attr = sort_attr
        self.value_attr = value_attr

        super().__init__()

    def _get(self, name: str, **sdk_options) -> str:
        """
        Retrieve a parameter value from Amazon DynamoDB

        Parameters
        ----------
        name: str
            Name of the parameter
        sdk_options: dict, optional
            Dictionary of options that will be passed to the DynamoDB get_item API call
        """

        # Explicit arguments will take precedence over keyword arguments
        sdk_options["Key"] = {self.key_attr: name}

        return self.table.get_item(**sdk_options)["Item"][self.value_attr]

    def _get_multiple(self, path: str, **sdk_options) -> Dict[str, str]:
        """
        Retrieve multiple parameter values from Amazon DynamoDB

        Parameters
        ----------
        path: str
            Path to retrieve the parameters
        sdk_options: dict, optional
            Dictionary of options that will be passed to the DynamoDB query API call
        """

        # Explicit arguments will take precedence over keyword arguments
        sdk_options["KeyConditionExpression"] = Key(self.key_attr).eq(path)

        response = self.table.query(**sdk_options)
        items = response.get("Items", [])

        # Keep querying while there are more items matching the partition key
        while "LastEvaluatedKey" in response:
            sdk_options["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            response = self.table.query(**sdk_options)
            items.extend(response.get("Items", []))

        return {item[self.sort_attr]: item[self.value_attr] for item in items}
