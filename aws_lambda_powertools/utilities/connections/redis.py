import logging
from typing import Optional, Type, Union

try:
    import redis  # type:ignore
except ImportError:
    redis = None

from .base_sync import BaseConnectionSync
from .exceptions import RedisConnectionError

logger = logging.getLogger(__name__)


class RedisConnection(BaseConnectionSync):
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        db_index: Optional[int] = None,
        url: Optional[str] = None,
        **extra_options,
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
        url: str, optional
            redis connection string, using url will override the host/port in the previous parameters
        extra_options: **kwargs, optional
            extra kwargs to pass directly into redis client
        """
        self.extra_options: dict = {}

        self.url = url
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_index = db_index
        self.extra_options.update(**extra_options)
        self._cluster_connection = None
        self._standalone_connection = None

    def _init_connection(self, client: Type[Union[redis.Redis, redis.cluster.RedisCluster]]):
        logger.info(f"Trying to connect to Redis: {self.host}")

        try:
            if self.url:
                logger.debug(f"Using URL format to connect to Redis: {self.host}")
                return client.from_url(url=self.url)
            else:
                logger.debug(f"Using other parameters to connect to Redis: {self.host}")
                return client(
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    db=self.db_index,
                    decode_responses=True,
                    **self.extra_options,
                )
        except redis.exceptions.ConnectionError as exc:
            logger.debug(f"Cannot connect in Redis: {self.host}")
            raise RedisConnectionError("Could not to connect to Redis", exc) from exc

    # simplified to use different func to get each connection.
    def get_standalone_connection(self) -> redis.Redis:
        """
        return a standalone redis client based on class's init parameter

        Returns
        -------
        Client:
            redis.Redis
        """
        if self._standalone_connection:
            return self._standalone_connection
        self._standalone_connection = self._init_connection(client=redis.Redis)
        return self._standalone_connection

    def get_cluster_connection(self) -> redis.cluster.RedisCluster:
        """
        return a cluster redis client based on class's init parameter
        if there are cached connection then return directly

        Returns
        -------
        Client:
            redis.cluster.RedisCluster
        """
        if self._cluster_connection:
            return self._cluster_connection
        self._cluster_connection = self._init_connection(client=redis.cluster.RedisCluster)
        return self._cluster_connection
