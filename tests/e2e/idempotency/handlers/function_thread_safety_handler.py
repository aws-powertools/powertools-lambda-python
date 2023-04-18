import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import current_thread

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    idempotent_function,
)

TABLE_NAME = os.getenv("IdempotencyTable", "")
persistence_layer = DynamoDBPersistenceLayer(table_name=TABLE_NAME)
threads_count = 2


@idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
def record_handler(record):
    time_now = time.time()
    return {"thread_name": current_thread().name, "time": str(time_now)}


def lambda_handler(event, context):
    with ThreadPoolExecutor(max_workers=threads_count) as executor:
        futures = [executor.submit(record_handler, **{"record": i}) for i in range(threads_count)]

    return [
        {"state": future._state, "exception": future.exception(), "output": future.result()}
        for future in as_completed(futures)
    ]
