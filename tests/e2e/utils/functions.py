import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import List

from tests.e2e.utils import data_fetcher  # noqa F401


def execute_lambdas_in_parallel(function_name: str, lambdas_arn: list, arguments: str):
    result_list = []
    with ThreadPoolExecutor() as executor:
        running_tasks: List[Future] = []
        for arn in lambdas_arn:
            # Sleep 0.5, 1, 1.5, ... seconds between each invocation. This way
            # we can guarantee that lambdas are executed in parallel, but they are
            # called in the same "order" as they are passed in, thus guaranteeing that
            # we can assert on the correct output.
            time.sleep(0.5 * len(running_tasks))
            running_tasks.append(
                executor.submit(
                    lambda lname, larn, largs: eval(lname)(larn, largs),
                    function_name,
                    arn,
                    arguments,
                )
            )

        executor.shutdown(wait=True)

        for running_task in running_tasks:
            result_list.append(running_task.result())

    return result_list
