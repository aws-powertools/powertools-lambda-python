import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import List

from tests.e2e.utils import data_fetcher  # noqa F401


def execute_lambdas_in_parallel(function_name: str, lambdas_arn: list, arguments: str):
    def f(function_name, arn, arguments):
        eval(function_name)(arn, arguments)

    result_list = []
    with ThreadPoolExecutor() as executor:
        running_tasks: List[Future] = []
        for arn in lambdas_arn:
            time.sleep(0.5 * len(running_tasks))
            running_tasks.append(executor.submit(f, function_name, arn, arguments))

        executor.shutdown(wait=True)

        for running_task in running_tasks:
            result_list.append(running_task.result())

    return result_list
