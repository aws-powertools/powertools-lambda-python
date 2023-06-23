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
        self.extra_options: dict = {}

        self.url = url
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_index = db_index
        self.extra_options.update(**extra_options)
        self._cluster_connection = None
        self._stdalone_connection = None

    def _init_connection(self, client: Type[Union[redis.Redis, redis.RedisCluster]]):
        """
        Connection is cached, so returning this
        """

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
    def get_standalone_connection(self):
        if self._stdalone_connection:
            return self._stdalone_connection
        return self._init_connection(client=redis.Redis)

    def get_cluster_connection(self):
        if self._cluster_connection:
            return self._cluster_connection
        return self._init_connection(client=redis.cluster.RedisCluster)
