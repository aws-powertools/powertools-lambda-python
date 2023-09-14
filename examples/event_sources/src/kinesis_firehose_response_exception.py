import base64

from aws_lambda_powertools.utilities.data_classes import (
    KinesisFirehoseDataTransformationRecord,
    KinesisFirehoseDataTransformationResponse,
)
from aws_lambda_powertools.utilities.serialization import base64_from_json
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext):
    result = KinesisFirehoseDataTransformationResponse()

    for record in event["records"]:
        print(record["recordId"])
        try:
            payload = base64.b64decode(record["data"]).decode("utf-8")
            ## do all kind of stuff with payload
            ## generate data to return
            transformed_data = {"tool_used": "powertools_dataclass", "original_payload": payload}
        except Exception:
            # add Failed result to processing results and send back to kinesis
            processed_record = KinesisFirehoseDataTransformationRecord(
                record_id=record["recordId"],
                data=base64_from_json(transformed_data),
                result="ProcessingFailed",
            )
            result.add_record(processed_record)
            continue

        # Default result is Ok
        processed_record = KinesisFirehoseDataTransformationRecord(
            record_id=record["recordId"],
            data=base64_from_json(transformed_data),
        )
        result.add_record(processed_record)

    # return transformed records
    return result.asdict()
