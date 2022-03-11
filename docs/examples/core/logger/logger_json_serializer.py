import orjson

from aws_lambda_powertools import Logger

custom_serializer = orjson.dumps
custom_deserializer = orjson.loads

logger = Logger(
    service="payment",
    json_serializer=custom_serializer,
    json_deserializer=custom_deserializer,
)

# when using parameters, you can pass a partial
# custom_serializer=functools.partial(orjson.dumps, option=orjson.OPT_SERIALIZE_NUMPY)
