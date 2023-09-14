from aws_lambda_powertools.utilities.data_classes import (
    KinesisFirehoseDataTransformationRecord,
    KinesisFirehoseDataTransformationResponse,
    KinesisFirehoseEvent,
)
from aws_lambda_powertools.utilities.serialization import base64_from_json
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext):
    firehose_event = KinesisFirehoseEvent(event)
    result = KinesisFirehoseDataTransformationResponse()

    for record in firehose_event.records:
        payload = record.data_as_text  # base64 decoded data as str

        ## generate data to return
        transformed_data = {"tool_used": "powertools_dataclass", "original_payload": payload}

        processed_record = KinesisFirehoseDataTransformationRecord(
            record_id=record.record_id,
            data=base64_from_json(transformed_data),
        )
        result.add_record(processed_record)

    # return transformed records
    return result.asdict()
