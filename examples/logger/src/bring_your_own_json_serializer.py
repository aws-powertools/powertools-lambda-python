import functools

import orjson

from aws_lambda_powertools import Logger

custom_serializer = orjson.dumps
custom_deserializer = orjson.loads

logger = Logger(service="payment", json_serializer=custom_serializer, json_deserializer=custom_deserializer)

# NOTE: when using parameters, you can pass a partial
custom_serializer_with_parameters = functools.partial(orjson.dumps, option=orjson.OPT_SERIALIZE_NUMPY)

logger_two = Logger(
    service="payment",
    json_serializer=custom_serializer_with_parameters,
    json_deserializer=custom_deserializer,
)
