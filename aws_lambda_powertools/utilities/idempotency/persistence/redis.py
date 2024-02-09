from __future__ import annotations

import datetime
import json
import logging
from contextlib import contextmanager
from datetime import timedelta
from typing import Any, Dict

import redis

from aws_lambda_powertools.shared.types import Literal, Protocol
from aws_lambda_powertools.utilities.idempotency import BasePersistenceLayer
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyItemAlreadyExistsError,
    IdempotencyItemNotFoundError,
    IdempotencyPersistenceConfigError,
    IdempotencyPersistenceConnectionError,
    IdempotencyPersistenceConsistencyError,
)
from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    STATUS_CONSTANTS,
    DataRecord,
)

logger = logging.getLogger(__name__)


class RedisClientProtocol(Protocol):
    """
    Protocol class defining the interface for a Redis client.

    This protocol outlines the expected behavior of a Redis client, allowing for
    standardization among different implementations and allowing customers to extend it
    in their own implementation.

    Methods
    -------
    - get(name: bytes | str | memoryview) -> bytes | str | None:
        Retrieves the value associated with the given key.

    - set(
        name: str | bytes,
        value: bytes | float | str,
        ex: float | timedelta | None = ...,
        px: float | timedelta | None = ...,
        nx: bool = ...,
    ) -> bool | None:
        Sets the value for the specified key with optional parameters.

    - delete(keys: bytes | str | memoryview) -> Any:
        Deletes one or more keys.

    Note
    ----
    - The `ex` parameter represents the expiration time in seconds.
    - The `px` parameter represents the expiration time in milliseconds.
    - The `nx` parameter, if True, sets the value only if the key does not exist.

    Raises
    ------
    - NotImplementedError: If any of the methods are not implemented by the concrete class.
    """

    def get(self, name: bytes | str | memoryview) -> bytes | str | None:
        raise NotImplementedError

    def set(  # noqa
        self,
        name: str | bytes,
        value: bytes | float | str,
        ex: float | timedelta | None = ...,
        px: float | timedelta | None = ...,
        nx: bool = ...,
    ) -> bool | None:
        raise NotImplementedError

    def delete(self, keys: bytes | str | memoryview) -> Any:
        raise NotImplementedError


class RedisConnection:
    def __init__(
        self,
        url: str = "",
        host: str = "",
        port: int = 6379,
        username: str = "",
        password: str = "",  # nosec - password for Redis connection
        db_index: int = 0,
        mode: Literal["standalone", "cluster"] = "standalone",
        ssl: bool = True,
    ) -> None:
        """
        Initialize Redis connection which will be used in Redis persistence_store to support Idempotency

        Parameters
        ----------
        host: str, optional
            Redis host
        port: int, optional: default 6379
            Redis port
        username: str, optional
            Redis username
        password: str, optional
            Redis password
        url: str, optional
            Redis connection string, using url will override the host/port in the previous parameters
        db_index: int, optional: default 0
            Redis db index
        mode: str, Literal["standalone","cluster"]
            set Redis client mode, choose from standalone/cluster. The default is standalone
        ssl: bool, optional: default True
            set whether to use ssl for Redis connection

        Examples
        --------

        ```python
        from dataclasses import dataclass, field
        from uuid import uuid4

        from aws_lambda_powertools.utilities.idempotency import (
            idempotent,
        )
        from aws_lambda_powertools.utilities.idempotency.persistence.redis import (
            RedisCachePersistenceLayer,
        )

        from aws_lambda_powertools.utilities.typing import LambdaContext

        persistence_layer = RedisCachePersistenceLayer(host="localhost", port=6379)


        @dataclass
        class Payment:
            user_id: str
            product_id: str
            payment_id: str = field(default_factory=lambda: f"{uuid4()}")


        class PaymentError(Exception):
            ...


        @idempotent(persistence_store=persistence_layer)
        def lambda_handler(event: dict, context: LambdaContext):
            try:
                payment: Payment = create_subscription_payment(event)
                return {
                    "payment_id": payment.payment_id,
                    "message": "success",
                    "statusCode": 200,
                }
            except Exception as exc:
                raise PaymentError(f"Error creating payment {str(exc)}")


        def create_subscription_payment(event: dict) -> Payment:
            return Payment(**event)

        ```
        """
        self.url = url
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_index = db_index
        self.ssl = ssl
        self.mode = mode

    def _init_client(self) -> RedisClientProtocol:
        logger.debug(f"Trying to connect to Redis: {self.host}")
        client: type[redis.Redis | redis.cluster.RedisCluster]
        if self.mode == "standalone":
            client = redis.Redis
        elif self.mode == "cluster":
            client = redis.cluster.RedisCluster
        else:
            raise IdempotencyPersistenceConfigError(f"Mode {self.mode} not supported")

        try:
            if self.url:
                logger.debug(f"Using URL format to connect to Redis: {self.host}")
                return client.from_url(url=self.url)
            else:
                # Redis in cluster mode doesn't support db parameter
                extra_param_connection: Dict[str, Any] = {}
                if self.mode != "cluster":
                    extra_param_connection = {"db": self.db_index}

                logger.debug(f"Using arguments to connect to Redis: {self.host}")
                return client(
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    decode_responses=True,
                    ssl=self.ssl,
                    **extra_param_connection,
                )
        except redis.exceptions.ConnectionError as exc:
            logger.debug(f"Cannot connect in Redis: {self.host}")
            raise IdempotencyPersistenceConnectionError("Could not to connect to Redis", exc) from exc


class RedisCachePersistenceLayer(BasePersistenceLayer):
    def __init__(
        self,
        url: str = "",
        host: str = "",
        port: int = 6379,
        username: str = "",
        password: str = "",  # nosec - password for Redis connection
        db_index: int = 0,
        mode: Literal["standalone", "cluster"] = "standalone",
        ssl: bool = True,
        client: RedisClientProtocol | None = None,
        in_progress_expiry_attr: str = "in_progress_expiration",
        expiry_attr: str = "expiration",
        status_attr: str = "status",
        data_attr: str = "data",
        validation_key_attr: str = "validation",
    ):
        """
        Initialize the Redis Persistence Layer

        Parameters
        ----------
        host: str, optional
            Redis host
        port: int, optional: default 6379
            Redis port
        username: str, optional
            Redis username
        password: str, optional
            Redis password
        url: str, optional
            Redis connection string, using url will override the host/port in the previous parameters
        db_index: int, optional: default 0
            Redis db index
        mode: str, Literal["standalone","cluster"]
            set Redis client mode, choose from standalone/cluster
        ssl: bool, optional: default True
            set whether to use ssl for Redis connection
        client: RedisClientProtocol, optional
            Bring your own Redis client that follows RedisClientProtocol.
            If provided, all other connection configuration options will be ignored
        expiry_attr: str, optional
            Redis json attribute name for expiry timestamp, by default "expiration"
        in_progress_expiry_attr: str, optional
            Redis json attribute name for in-progress expiry timestamp, by default "in_progress_expiration"
        status_attr: str, optional
            Redis json attribute name for status, by default "status"
        data_attr: str, optional
            Redis json attribute name for response data, by default "data"
        validation_key_attr: str, optional
            Redis json attribute name for hashed representation of the parts of the event used for validation

        Examples
        --------

        ```python
        from redis import Redis
        from aws_lambda_powertools.utilities.idempotency import (
            idempotent,
        )

        from aws_lambda_powertools.utilities.idempotency.persistence.redis import (
            RedisCachePersistenceLayer,
        )

        client = redis.Redis(
            host="localhost",
            port="6379",
            decode_responses=True,
        )
        persistence_layer = RedisCachePersistenceLayer(client=client)

        @idempotent(persistence_store=persistence_layer)
        def lambda_handler(event: dict, context: LambdaContext):
            print("expensive operation")
            return {
                "payment_id": 12345,
                "message": "success",
                "statusCode": 200,
            }
        ```
        """

        # Initialize Redis client with Redis config if no client is passed in
        if client is None:
            self.client = RedisConnection(
                host=host,
                port=port,
                username=username,
                password=password,
                db_index=db_index,
                url=url,
                mode=mode,
                ssl=ssl,
            )._init_client()
        else:
            self.client = client

        self.in_progress_expiry_attr = in_progress_expiry_attr
        self.expiry_attr = expiry_attr
        self.status_attr = status_attr
        self.data_attr = data_attr
        self.validation_key_attr = validation_key_attr
        self._json_serializer = json.dumps
        self._json_deserializer = json.loads
        super(RedisCachePersistenceLayer, self).__init__()
        self._orphan_lock_timeout = min(10, self.expires_after_seconds)

    def _get_expiry_second(self, expiry_timestamp: int | None = None) -> int:
        """
        Calculates the number of seconds remaining until a specified expiry time
        """
        if expiry_timestamp:
            return expiry_timestamp - int(datetime.datetime.now().timestamp())
        return self.expires_after_seconds

    def _item_to_data_record(self, idempotency_key: str, item: Dict[str, Any]) -> DataRecord:
        in_progress_expiry_timestamp = item.get(self.in_progress_expiry_attr)

        return DataRecord(
            idempotency_key=idempotency_key,
            status=item[self.status_attr],
            in_progress_expiry_timestamp=in_progress_expiry_timestamp,
            response_data=str(item.get(self.data_attr)),
            payload_hash=str(item.get(self.validation_key_attr)),
            expiry_timestamp=item.get("expiration", None),
        )

    def _get_record(self, idempotency_key) -> DataRecord:
        # See: https://redis.io/commands/get/
        response = self.client.get(idempotency_key)

        # key not found
        if not response:
            raise IdempotencyItemNotFoundError

        try:
            item = self._json_deserializer(response)
        except json.JSONDecodeError:
            # Json decoding error is considered an Consistency error. This scenario will also introduce possible
            # race condition just like Orphan record does. As two lambda handlers is possible to reach this line
            # of code almost simultaneously. If we simply regard this record as non-valid record. The two lambda
            # handlers will both start the overwrite process without knowing each other. Causing this value being
            # overwritten twice (ultimately two Lambda Handlers will both be executed, which is against idempotency).
            # So this case should also be handled by the error handling in IdempotencyPersistenceConsistencyError
            # part to avoid the possible race condition.

            raise IdempotencyPersistenceConsistencyError

        return self._item_to_data_record(idempotency_key, item)

    def _put_in_progress_record(self, data_record: DataRecord) -> None:
        item: Dict[str, Any] = {
            "name": data_record.idempotency_key,
            "mapping": {
                self.status_attr: data_record.status,
                self.expiry_attr: data_record.expiry_timestamp,
            },
        }

        if data_record.in_progress_expiry_timestamp is not None:
            item["mapping"][self.in_progress_expiry_attr] = data_record.in_progress_expiry_timestamp

        if self.payload_validation_enabled:
            item["mapping"][self.validation_key_attr] = data_record.payload_hash

        now = datetime.datetime.now()
        try:
            # |     LOCKED     |         RETRY if status = "INPROGRESS"                |     RETRY
            # |----------------|-------------------------------------------------------|-------------> .... (time)
            # |             Lambda                                              Idempotency Record
            # |             Timeout                                                 Timeout
            # |       (in_progress_expiry)                                          (expiry)

            # Conditions to successfully save a record:

            # The idempotency key does not exist:
            #    - first time that this invocation key is used
            #    - previous invocation with the same key was deleted due to TTL
            #    - SET see https://redis.io/commands/set/

            logger.debug(f"Putting record on Redis for idempotency key: {data_record.idempotency_key}")
            encoded_item = self._json_serializer(item["mapping"])
            ttl = self._get_expiry_second(expiry_timestamp=data_record.expiry_timestamp)

            redis_response = self.client.set(name=data_record.idempotency_key, value=encoded_item, ex=ttl, nx=True)

            # If redis_response is True, the Redis SET operation was successful and the idempotency key was not
            # previously set. This indicates that we can safely proceed to the handler execution phase.
            # Most invocations should successfully proceed past this point.
            if redis_response:
                return

            # If redis_response is None, it indicates an existing record in Redis for the given idempotency key.
            # This could be due to:
            # - An active idempotency record from a previous invocation that has not yet expired.
            # - An orphan record where a previous invocation has timed out.
            # - An expired idempotency record that has not been deleted by Redis.
            # In any case, we proceed to retrieve the record for further inspection.

            idempotency_record = self._get_record(data_record.idempotency_key)

            # If the status of the idempotency record is 'COMPLETED' and the record has not expired
            # (i.e., the expiry timestamp is greater than the current timestamp), then a valid completed
            # record exists. We raise an error to prevent duplicate processing of a request that has already
            # been completed successfully.
            if idempotency_record.status == STATUS_CONSTANTS["COMPLETED"] and not idempotency_record.is_expired:
                raise IdempotencyItemAlreadyExistsError

            # If the idempotency record has a status of 'INPROGRESS' and has a valid in_progress_expiry_timestamp
            # (meaning the timestamp is greater than the current timestamp in milliseconds), then we have encountered
            # a valid in-progress record. This indicates that another process is currently handling the request, and
            # to maintain idempotency, we raise an error to prevent concurrent processing of the same request.
            if (
                idempotency_record.status == STATUS_CONSTANTS["INPROGRESS"]
                and idempotency_record.in_progress_expiry_timestamp
                and idempotency_record.in_progress_expiry_timestamp > int(now.timestamp() * 1000)
            ):
                raise IdempotencyItemAlreadyExistsError

            # Reaching this point indicates that the idempotency record found is an orphan record. An orphan record is
            # one that is neither completed nor in-progress within its expected time frame. It may result from a
            # previous invocation that has timed out or an expired record that has yet to be cleaned up by Redis.
            # We raise an error to handle this exceptional scenario appropriately.
            raise IdempotencyPersistenceConsistencyError

        except IdempotencyPersistenceConsistencyError:
            # Handle an orphan record by attempting to acquire a lock, which by default lasts for 10 seconds.
            # The purpose of acquiring the lock is to prevent race conditions with other processes that might
            # also be trying to handle the same orphan record. Once the lock is acquired, we set a new value
            # for the idempotency record in Redis with the appropriate time-to-live (TTL).
            with self._acquire_lock(name=item["name"]):
                self.client.set(name=item["name"], value=encoded_item, ex=ttl)

            # Not removing the lock here serves as a safeguard against race conditions,
            # preventing another operation from mistakenly treating this record as an orphan while the
            # current operation is still in progress.
        except (redis.exceptions.RedisError, redis.exceptions.RedisClusterException) as e:
            raise e
        except Exception as e:
            logger.debug(f"encountered non-Redis exception: {e}")
            raise e

    @contextmanager
    def _acquire_lock(self, name: str):
        """
        Attempt to acquire a lock for a specified resource name, with a default timeout.
        This context manager attempts to set a lock using Redis to prevent concurrent
        access to a resource identified by 'name'. It uses the 'nx' flag to ensure that
        the lock is only set if it does not already exist, thereby enforcing mutual exclusion.
        """
        try:
            acquired = self.client.set(name=f"{name}:lock", value="True", ex=self._orphan_lock_timeout, nx=True)
            logger.debug("acquiring lock to overwrite orphan record")
            if acquired:
                logger.debug("lock acquired")
                yield
            else:
                # If the lock acquisition fails, it suggests a race condition has occurred. In this case, instead of
                # proceeding, we log the event and raise an error to indicate that the current operation should be
                # retried after the lock is released by the process that currently holds it.
                logger.debug("lock acquisition failed, raise to retry")
                raise IdempotencyItemAlreadyExistsError

        finally:
            ...

    def _put_record(self, data_record: DataRecord) -> None:
        if data_record.status == STATUS_CONSTANTS["INPROGRESS"]:
            self._put_in_progress_record(data_record=data_record)
        else:
            # current this function only support set in_progress. set complete should use update_record
            raise NotImplementedError

    def _update_record(self, data_record: DataRecord) -> None:
        item: Dict[str, Any] = {
            "name": data_record.idempotency_key,
            "mapping": {
                self.data_attr: data_record.response_data,
                self.status_attr: data_record.status,
                self.expiry_attr: data_record.expiry_timestamp,
            },
        }
        logger.debug(f"Updating record for idempotency key: {data_record.idempotency_key}")
        encoded_item = self._json_serializer(item["mapping"])
        ttl = self._get_expiry_second(data_record.expiry_timestamp)
        # need to set ttl again, if we don't set ex here the record will not have a ttl
        self.client.set(name=item["name"], value=encoded_item, ex=ttl)

    def _delete_record(self, data_record: DataRecord) -> None:
        """
        Deletes the idempotency record associated with a given DataRecord from Redis.
        This function is designed to be called after a Lambda handler invocation has completed processing.
        It ensures that the idempotency key associated with the DataRecord is removed from Redis to
        prevent future conflicts and to maintain the idempotency integrity.

        Note: it is essential that the idempotency key is not empty, as that would indicate the Lambda
        handler has not been invoked or the key was not properly set.
        """
        logger.debug(f"Deleting record for idempotency key: {data_record.idempotency_key}")

        # See: https://redis.io/commands/del/
        self.client.delete(data_record.idempotency_key)
