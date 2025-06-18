from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.kafka.consumer_records import ConsumerRecords

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.kafka.schema_config import SchemaConfig
    from aws_lambda_powertools.utilities.typing import LambdaContext


@lambda_handler_decorator
def kafka_consumer(
    handler: Callable[[Any, LambdaContext], Any],
    event: dict[str, Any],
    context: LambdaContext,
    schema_config: SchemaConfig | None = None,
):
    """
    Decorator for processing Kafka consumer records in AWS Lambda functions.

    This decorator transforms the raw Lambda event into a ConsumerRecords object,
    making it easier to process Kafka messages with optional schema validation
    and deserialization.

    Parameters
    ----------
    handler : Callable[[Any, LambdaContext], Any]
        The Lambda handler function being decorated.
    event : dict[str, Any]
        The Lambda event containing Kafka records.
    context : LambdaContext
        The Lambda context object.
    schema_config : SchemaConfig, optional
        Schema configuration for deserializing Kafka records.
        Must be an instance of SchemaConfig.

    Returns
    -------
    Any
        The return value from the handler function.

    Examples
    --------
    >>> from aws_lambda_powertools.utilities.kafka import kafka_consumer, SchemaConfig
    >>>
    >>> # With schema validation using SchemaConfig
    >>> schema_config = SchemaConfig(value_schema_type="JSON")
    >>>
    >>> @kafka_consumer(schema_config=schema_config)
    >>> def handler_with_schema(records, context):
    >>>     for record in records:
    >>>         # record.value will be automatically deserialized according to schema_config
    >>>         process_message(record.value)
    >>>     return {"statusCode": 200}
    """
    return handler(ConsumerRecords(event, schema_config), context)
