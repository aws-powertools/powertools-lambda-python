"""
DynamoDB persistence backend for the Circuit Breaker utility.
"""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

import boto3
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError

from aws_lambda_powertools.shared import user_agent
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.base import (
    CircuitBreakerExistingLockError,
    CircuitBreakerPersistenceLayer,
    CircuitBreakerRecordNotFoundError,
)
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.record import CircuitStateRecord
from aws_lambda_powertools.utilities.circuit_breaker_alpha.states import CircuitState

if TYPE_CHECKING:
    from botocore.config import Config
    from mypy_boto3_dynamodb.client import DynamoDBClient

logger = logging.getLogger(__name__)


class CircuitBreakerDynamoDBPersistence(CircuitBreakerPersistenceLayer):
    """
    Store circuit state in an Amazon DynamoDB table, one item per circuit.

    The class name is prefixed with ``CircuitBreaker`` so a function using both the
    Idempotency and Circuit Breaker utilities can import both persistence layers
    without an alias.

    Parameters
    ----------
    table_name : str
        Name of the DynamoDB table that stores circuit state.
    key_attr : str
        Partition key attribute holding the circuit name. Defaults to ``"id"``.
    state_attr : str
        Attribute holding the circuit state. Defaults to ``"state"``.
    failure_count_attr : str
        Attribute holding the consecutive failure count. Defaults to ``"failure_count"``.
    opened_at_attr : str
        Attribute holding the open timestamp. Defaults to ``"opened_at"``.
    half_open_owner_attr : str
        Attribute holding the half-open probe lock owner. Defaults to ``"half_open_owner"``.
    probe_lease_expiry_attr : str
        Attribute holding the probe lease expiry timestamp. Defaults to ``"probe_lease_expiry"``.
    expiry_attr : str
        TTL attribute. Defaults to ``"expiration"``.
    boto_config : botocore.config.Config, optional
        Botocore configuration used when creating the client.
    boto3_session : boto3.session.Session, optional
        Session used to create the client.
    boto3_client : DynamoDBClient, optional
        Pre-built client; ``boto3_session`` and ``boto_config`` are ignored if given.

    Example
    -------
    **Create a DynamoDB-backed circuit breaker store**

        from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence import (
            CircuitBreakerDynamoDBPersistence,
        )

        persistence = CircuitBreakerDynamoDBPersistence(table_name="CircuitBreakerState")
    """

    def __init__(
        self,
        table_name: str,
        key_attr: str = "id",
        state_attr: str = "state",
        failure_count_attr: str = "failure_count",
        opened_at_attr: str = "opened_at",
        half_open_owner_attr: str = "half_open_owner",
        probe_lease_expiry_attr: str = "probe_lease_expiry",
        expiry_attr: str = "expiration",
        boto_config: Config | None = None,
        boto3_session: boto3.session.Session | None = None,
        boto3_client: DynamoDBClient | None = None,
    ):
        if boto3_client is None:
            boto3_session = boto3_session or boto3.session.Session()
            boto3_client = boto3_session.client("dynamodb", config=boto_config)
        self.client = boto3_client

        user_agent.register_feature_to_client(client=self.client, feature="circuit_breaker")

        self.table_name = table_name
        self.key_attr = key_attr
        self.state_attr = state_attr
        self.failure_count_attr = failure_count_attr
        self.opened_at_attr = opened_at_attr
        self.half_open_owner_attr = half_open_owner_attr
        self.probe_lease_expiry_attr = probe_lease_expiry_attr
        self.expiry_attr = expiry_attr

        self._deserializer = TypeDeserializer()

        super().__init__()

    def _item_to_record(self, item: dict) -> CircuitStateRecord:
        """Translate a raw DynamoDB item into a :class:`CircuitStateRecord`."""
        data = self._deserializer.deserialize({"M": item})
        opened_at = data.get(self.opened_at_attr)
        probe_lease_expiry = data.get(self.probe_lease_expiry_attr)
        return CircuitStateRecord(
            name=data[self.key_attr],
            state=CircuitState(data[self.state_attr]),
            failure_count=int(data.get(self.failure_count_attr, 0)),
            opened_at=int(opened_at) if opened_at is not None else None,
            half_open_owner=data.get(self.half_open_owner_attr),
            probe_lease_expiry=int(probe_lease_expiry) if probe_lease_expiry is not None else None,
            expiry_timestamp=data.get(self.expiry_attr),
        )

    def _record_to_item(self, record: CircuitStateRecord) -> dict:
        """Translate a :class:`CircuitStateRecord` into a DynamoDB item."""
        item: dict = {
            self.key_attr: {"S": record.name},
            self.state_attr: {"S": str(record.state)},
            self.failure_count_attr: {"N": str(record.failure_count)},
        }
        if record.opened_at is not None:
            item[self.opened_at_attr] = {"N": str(record.opened_at)}
        if record.half_open_owner is not None:
            item[self.half_open_owner_attr] = {"S": record.half_open_owner}
        if record.probe_lease_expiry is not None:
            item[self.probe_lease_expiry_attr] = {"N": str(record.probe_lease_expiry)}
        if record.expiry_timestamp is not None:
            item[self.expiry_attr] = {"N": str(record.expiry_timestamp)}
        return item

    def _get_record(self, name: str) -> CircuitStateRecord:
        # Eventually consistent on purpose: matches the local cache's stale tolerance
        # and halves the read cost on the hot path.
        response = self.client.get_item(
            TableName=self.table_name,
            Key={self.key_attr: {"S": name}},
            ConsistentRead=False,
        )
        try:
            item = response["Item"]
        except KeyError as exc:
            raise CircuitBreakerRecordNotFoundError from exc
        return self._item_to_record(item)

    def _build_half_open_condition(self, expected_opened_at: int | None = None) -> dict:
        """Build the conditional expression kwargs for a half-open probe election."""
        condition_parts = [
            "(#state = :open AND attribute_not_exists(#half_open_owner))",
            "(#state = :half_open AND #probe_lease_expiry <= :now)",
        ]
        expression_attr_names: dict = {
            "#state": self.state_attr,
            "#half_open_owner": self.half_open_owner_attr,
            "#probe_lease_expiry": self.probe_lease_expiry_attr,
        }
        expression_values: dict = {
            ":open": {"S": str(CircuitState.OPEN)},
            ":half_open": {"S": str(CircuitState.HALF_OPEN)},
            ":now": {"N": str(int(datetime.datetime.now().timestamp()))},
        }

        if expected_opened_at is not None:
            condition_parts[0] = (
                "(#state = :open AND attribute_not_exists(#half_open_owner) AND #opened_at = :expected_opened_at)"
            )
            expression_attr_names["#opened_at"] = self.opened_at_attr
            expression_values[":expected_opened_at"] = {"N": str(expected_opened_at)}

        return {
            "ConditionExpression": " OR ".join(condition_parts),
            "ExpressionAttributeNames": expression_attr_names,
            "ExpressionAttributeValues": expression_values,
        }

    def _put_record(
        self,
        record: CircuitStateRecord,
        condition: str | None = None,
        expected_opened_at: int | None = None,
    ) -> None:
        item = self._record_to_item(record)

        put_kwargs: dict = {"TableName": self.table_name, "Item": item}

        if condition == "half_open":
            put_kwargs.update(self._build_half_open_condition(expected_opened_at))

        try:
            self.client.put_item(**put_kwargs)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise CircuitBreakerExistingLockError from exc
            raise

    def _update_record(self, record: CircuitStateRecord) -> None:
        update_expression = "SET #state = :state, #failure_count = :failure_count"
        expression_attr_names = {
            "#state": self.state_attr,
            "#failure_count": self.failure_count_attr,
        }
        expression_attr_values: dict = {
            ":state": {"S": str(record.state)},
            ":failure_count": {"N": str(record.failure_count)},
        }

        if record.expiry_timestamp is not None:
            update_expression += ", #expiration = :expiration"
            expression_attr_names["#expiration"] = self.expiry_attr
            expression_attr_values[":expiration"] = {"N": str(record.expiry_timestamp)}

        # Clear the half-open owner lock and probe lease on every state change out of
        # HALF_OPEN, whether the probe closed the circuit (opened_at is None) or reopened
        # it (opened_at set). Otherwise the stale owner/lease makes the next probe
        # election's condition fail forever, stranding the circuit.
        if record.opened_at is not None:
            update_expression += ", #opened_at = :opened_at REMOVE #half_open_owner, #probe_lease_expiry"
            expression_attr_names["#opened_at"] = self.opened_at_attr
            expression_attr_names["#half_open_owner"] = self.half_open_owner_attr
            expression_attr_names["#probe_lease_expiry"] = self.probe_lease_expiry_attr
            expression_attr_values[":opened_at"] = {"N": str(record.opened_at)}
        else:
            update_expression += " REMOVE #opened_at, #half_open_owner, #probe_lease_expiry"
            expression_attr_names["#opened_at"] = self.opened_at_attr
            expression_attr_names["#half_open_owner"] = self.half_open_owner_attr
            expression_attr_names["#probe_lease_expiry"] = self.probe_lease_expiry_attr

        self.client.update_item(
            TableName=self.table_name,
            Key={self.key_attr: {"S": record.name}},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attr_names,
            ExpressionAttributeValues=expression_attr_values,
        )
