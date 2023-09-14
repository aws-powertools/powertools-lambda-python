from aws_lambda_powertools.utilities.data_classes import (
    KinesisFirehoseDataTransformationRecord,
    KinesisFirehoseDataTransformationResponse,
    KinesisFirehoseEvent,
    event_source,
)
from aws_lambda_powertools.utilities.serialization import base64_from_json
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=KinesisFirehoseEvent)
def lambda_handler(event: dict, context: LambdaContext):
    firehose_event = KinesisFirehoseEvent(event)
    result = KinesisFirehoseDataTransformationResponse()

    for record in firehose_event.records:
        try:
            payload = record.data_as_text  # base64 decoded data as str

            # generate data to return
            transformed_data = {"tool_used": "powertools_dataclass", "original_payload": payload}

            # Default result is Ok
            processed_record = KinesisFirehoseDataTransformationRecord(
                record_id=record.record_id,
                data=base64_from_json(transformed_data),
            )
        except Exception:
            # add Failed result to processing results, send back to kinesis for retry
            processed_record = KinesisFirehoseDataTransformationRecord(
                record_id=record.record_id,
                data=record.data,
                result="ProcessingFailed",  # (1)!
            )

        result.add_record(processed_record)

    # return transformed records
    return result.asdict()
