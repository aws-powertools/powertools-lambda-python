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
        payload = base64.b64decode(record["data"]).decode("utf-8")
        ## do all kind of stuff with payload
        ## generate data to return
        transformed_data = {"tool_used": "powertools_dataclass", "original_payload": payload}

        processed_record = KinesisFirehoseDataTransformationRecord(
            record_id=record["recordId"],
            result="Ok",
            data=base64_from_json(transformed_data),
        )
        result.add_record(processed_record)

    # return transformed records
    return result.asdict()
