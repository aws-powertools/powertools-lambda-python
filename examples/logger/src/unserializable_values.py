from datetime import date, datetime

from aws_lambda_powertools import Logger


def custom_json_default(value: object) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    return f"<non-serializable: {type(value).__name__}>"


class Unserializable:
    pass


logger = Logger(service="payment", json_default=custom_json_default)

logger.info({"ingestion_time": datetime.utcnow(), "serialize_me": Unserializable()})
