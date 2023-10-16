from __future__ import annotations

import datetime
import logging
from typing import Any, Dict

import redis
from typing_extensions import Literal

from aws_lambda_powertools.utilities.idempotency import BasePersistenceLayer
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyItemAlreadyExistsError,
    IdempotencyItemNotFoundError,
    IdempotencyRedisClientConfigError,
    IdempotencyRedisConnectionError,
)
from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    STATUS_CONSTANTS,
    DataRecord,
)

logger = logging.getLogger(__name__)


class RedisConnection:
    def __init__(
        self,
        host: str | None,
        username: str | None,
        password: str | None,
        url: str | None,
        db_index: int = 0,
        port: int = 6379,
        mode: Literal["standalone", "cluster"] = "standalone",
    ) -> None:
        """
        Initialize Redis connection which will be used in redis persistence_store to support idempotency

        Parameters
        ----------
        host: str, optional
            redis host
        port: int, optional
            redis port
        username: str, optional
            redis username
        password: str, optional
            redis password
        db_index: str, optional
            redis db index
        mode: str, Literal["standalone","cluster"]
            set redis client mode, choose from standalone/cluster
        url: str, optional
            redis connection string, using url will override the host/port in the previous parameters
        extra_options: **kwargs, optional
            extra kwargs to pass directly into redis client

        Examples
        --------

        ```python
        from dataclasses import dataclass, field
        from uuid import uuid4

        from aws_lambda_powertools.utilities.idempotency import (
            RedisCachePersistenceLayer,
            RedisConfig,
            idempotent,
        )
        from aws_lambda_powertools.utilities.typing import LambdaContext

        config = RedisConfig(host="localhost", port="6379, mode="standalone")

        persistence_layer = RedisCachePersistenceLayer(config=config)


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
        self.mode = mode

    def _init_client(self) -> redis.Redis | redis.cluster.RedisCluster:
        logger.info(f"Trying to connect to Redis: {self.host}")
        if self.mode == "standalone":
            client = redis.Redis
        elif self.mode == "cluster":
            client = redis.cluster.RedisCluster
        else:
            raise IdempotencyRedisClientConfigError(f"Mode {self.mode} not supported")

        try:
            if self.url:
                logger.debug(f"Using URL format to connect to Redis: {self.host}")
                return client.from_url(url=self.url)
            else:
                logger.debug(f"Using other parameters to connect to Redis: {self.host}")
                return client(  # type: ignore
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    db=self.db_index,
                    decode_responses=True,
                )
        except redis.exceptions.ConnectionError as exc:
            logger.debug(f"Cannot connect in Redis: {self.host}")
            raise IdempotencyRedisConnectionError("Could not to connect to Redis", exc) from exc


class RedisCachePersistenceLayer(BasePersistenceLayer):
    def __init__(
        self,
        host: str | None = None,
        username: str | None = None,
        password: str | None = None,
        url: str | None = None,
        db_index: int = 0,
        port: int = 6379,
        mode: Literal["standalone", "cluster"] = "standalone",
        client: redis.Redis | redis.cluster.RedisCluster | None = None,
        in_progress_expiry_attr: str = "in_progress_expiration",
        status_attr: str = "status",
        data_attr: str = "data",
        validation_key_attr: str = "validation",
    ):
        """
        Initialize the Redis Persistence Layer
        Parameters
        ----------
        client: Union[redis.Redis, redis.cluster.RedisCluster], optional
            You can bring your established Redis client.
            If client is provided, config will be ignored
        config: RedisConfig, optional
            If client is not provided, config will be parsed and a corresponding
            Redis client will be created.
        in_progress_expiry_attr: str, optional
            Redis hash attribute name for in-progress expiry timestamp, by default "in_progress_expiration"
        status_attr: str, optional
            Redis hash attribute name for status, by default "status"
        data_attr: str, optional
            Redis hash attribute name for response data, by default "data"
        validation_key_attr: str, optional
            Redis hash attribute name for hashed representation of the parts of the event used for validation

        Examples
        --------

        ```python
        from redis import Redis
        from aws_lambda_powertools.utilities.data_class import(
            RedisCachePersistenceLayer,
        )
        from aws_lambda_powertools.utilities.idempotency.idempotency import (
            idempotent,
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
            )._init_client()
        else:
            self.client = client

        if not hasattr(self.client, "get_connection_kwargs"):
            raise IdempotencyRedisClientConfigError
        if not self.client.get_connection_kwargs().get("decode_responses", False):
            # Requires decode_responses to be true
            raise IdempotencyRedisClientConfigError

        self.in_progress_expiry_attr = in_progress_expiry_attr
        self.status_attr = status_attr
        self.data_attr = data_attr
        self.validation_key_attr = validation_key_attr
        super(RedisCachePersistenceLayer, self).__init__()

    def _item_to_data_record(self, idempotency_key: str, item: Dict[str, Any]) -> DataRecord:
        in_progress_expiry_timestamp = item.get(self.in_progress_expiry_attr)
        if isinstance(in_progress_expiry_timestamp, str):
            in_progress_expiry_timestamp = int(in_progress_expiry_timestamp)
        return DataRecord(
            idempotency_key=idempotency_key,
            status=item[self.status_attr],
            in_progress_expiry_timestamp=in_progress_expiry_timestamp,
            response_data=str(item.get(self.data_attr)),
            payload_hash=str(item.get(self.validation_key_attr)),
        )

    def _get_record(self, idempotency_key) -> DataRecord:
        # See: https://redis.io/commands/hgetall/
        response = self.client.hgetall(idempotency_key)

        try:
            item = response
        except KeyError:
            raise IdempotencyItemNotFoundError
        return self._item_to_data_record(idempotency_key, item)

    def _put_record(self, data_record: DataRecord) -> None:
        item: Dict[str, Any] = {}

        # Redis works with hset to support hashing keys with multiple attributes
        # See: https://redis.io/commands/hset/
        item = {
            "name": data_record.idempotency_key,
            "mapping": {
                self.status_attr: data_record.status,
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
            idempotency_record = self.client.hgetall(data_record.idempotency_key)
            print(idempotency_record)
            if len(idempotency_record) > 0:
                # record already exists.

                # status is completed, so raise exception because it exists and still valid
                if idempotency_record[self.status_attr] == STATUS_CONSTANTS["COMPLETED"]:
                    raise IdempotencyItemAlreadyExistsError

                # checking if in_progress_expiry_attr exists
                # if in_progress_expiry_attr exist, must be lower than now
                if self.in_progress_expiry_attr in idempotency_record and int(
                    idempotency_record[self.in_progress_expiry_attr],
                ) > int(now.timestamp() * 1000):
                    raise IdempotencyItemAlreadyExistsError

            logger.debug(f"Putting record on Redis for idempotency key: {data_record.idempotency_key}")
            self.client.hset(**item)
            # hset type must set expiration after adding the record
            # Need to review this to get ttl in seconds
            # Q: should we replace self.expires_after_seconds with _get_expiry_timestamp? more consistent
            self.client.expire(name=data_record.idempotency_key, time=self.expires_after_seconds)
        except redis.exceptions.RedisError:
            raise redis.exceptions.RedisError
        except redis.exceptions.RedisClusterException:
            raise redis.exceptions.RedisClusterException
        except Exception as e:
            logger.debug(f"encountered non-redis exception:{e}")
            raise e

    def _update_record(self, data_record: DataRecord) -> None:
        item: Dict[str, Any] = {}

        item = {
            "name": data_record.idempotency_key,
            "mapping": {
                self.data_attr: data_record.response_data,
                self.status_attr: data_record.status,
            },
        }
        logger.debug(f"Updating record for idempotency key: {data_record.idempotency_key}")
        self.client.hset(**item)

    def _delete_record(self, data_record: DataRecord) -> None:
        # This function only works when Lambda handler has already been invoked once
        # maybe we should add some exception when this is called before Lambda handler
        logger.debug(f"Deleting record for idempotency key: {data_record.idempotency_key}")
        # See: https://redis.io/commands/del/
        self.client.delete(data_record.idempotency_key)
