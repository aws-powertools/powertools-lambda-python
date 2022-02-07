from typing import Dict, List, Optional


class BatchResponse:
    """Batch Response

    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html#services-sqs-batchfailurereporting
    - https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis.html#services-kinesis-batchfailurereporting
    - https://docs.aws.amazon.com/lambda/latest/dg/with-ddb.html#services-ddb-batchfailurereporting
    """

    def __init__(self, failed_items: Optional[List[str]] = None) -> None:
        if failed_items:
            self._messages = [{"itemIdentifier": item} for item in failed_items]
        else:
            self._messages = []

    def add_item(self, identifier: str):
        self._messages.append({"itemIdentifier": identifier})

    def asdict(self) -> Dict[str, List]:
        return {"batchItemFailures": self._messages}
