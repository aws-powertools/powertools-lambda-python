from json import JSONDecodeError
from typing import Dict

from aws_lambda_powertools.utilities.data_classes import (
    KinesisFirehoseDataTransformationRecord,
    KinesisFirehoseDataTransformationResponse,
    KinesisFirehoseEvent,
    event_source,
)
from aws_lambda_powertools.utilities.serialization import base64_from_json
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=KinesisFirehoseEvent)
def lambda_handler(event: KinesisFirehoseEvent, context: LambdaContext):
    result = KinesisFirehoseDataTransformationResponse()

    for record in event.records:
        try:
            payload: Dict = record.data_as_json  # decodes and deserialize base64 JSON string

            ## generate data to return
            transformed_data = {"tool_used": "powertools_dataclass", "original_payload": payload}

            processed_record = KinesisFirehoseDataTransformationRecord(
                record_id=record.record_id,
                data=base64_from_json(transformed_data),
            )
        except JSONDecodeError:  # (1)!
            # our producers ingest JSON payloads only; drop malformed records from the stream
            processed_record = KinesisFirehoseDataTransformationRecord(
                record_id=record.record_id,
                data=record.data,
                result="Dropped",
            )

        result.add_record(processed_record)

    # return transformed records
    return result.asdict()
