docker run --name redis_master -p 6379:6379 -d redis
docker run --name redis_slave_1 -p 6380:6380  --link redis_master:redis_master -d redis redis-server  --slaveof redis_master 6379
docker run --name redis_slave_2 -p 6381:6381 --link redis_master:redis_master -d redis redis-server  --slaveof redis_master 6379
docker run --name redis_slave_3 -p 6382:6382  --link redis_master:redis_master -d redis redis-server  --slaveof redis_master 6379
docker run --name redis_sentinel_1 -d -e REDIS_MASTER_HOST=redis_master -e REDIS_SENTINEL_PORT_NUMBER=26379 -e REDIS_SENTINEL_QUORUM=2 -p 26379:26379  --link redis_master:redis_master bitnami/redis-sentinel:latest
docker run --name redis_sentinel_2 -d -e REDIS_MASTER_HOST=redis_master -e REDIS_SENTINEL_PORT_NUMBER=26380 -e REDIS_SENTINEL_QUORUM=2 -p 26380:26380  --link redis_master:redis_master bitnami/redis-sentinel:latest
docker run --name redis_sentinel_3 -d -e REDIS_MASTER_HOST=redis_master -e REDIS_SENTINEL_PORT_NUMBER=26381 -e REDIS_SENTINEL_QUORUM=2 -p 26381:26381 --link redis_master:redis_master bitnami/redis-sentinel:latest
