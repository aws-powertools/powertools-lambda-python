from concurrent.futures import ThreadPoolExecutor

from tests.e2e.utils import data_fetcher  # noqa F401


def execute_lambdas_in_parallel(function_name: str, lambdas_arn: list, arguments: str):
    result_list = []
    with ThreadPoolExecutor() as executor:
        running_tasks = executor.map(lambda exec: eval(function_name)(*exec), [(arn, arguments) for arn in lambdas_arn])
        executor.shutdown(wait=True)
        for running_task in running_tasks:
            result_list.append(running_task)

    return result_list
