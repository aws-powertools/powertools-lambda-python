import threading
from typing import List

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def threaded_func(order_id: str):
    logger.thread_safe_append_keys(order_id=order_id, thread_id=threading.get_ident())
    logger.info("Collecting payment")


def lambda_handler(event: dict, context: LambdaContext) -> str:
    order_ids: List[str] = event["order_ids"]

    threading.Thread(target=threaded_func, args=(order_ids[0],)).start()
    threading.Thread(target=threaded_func, args=(order_ids[1],)).start()

    return "hello world"
