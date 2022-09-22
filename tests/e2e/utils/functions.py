from concurrent.futures import ThreadPoolExecutor


def execute_lambdas_in_parallel(tasks, arguments):
    result_list = []
    with ThreadPoolExecutor() as executor:
        running_tasks = [executor.submit(task, **arguments) for task in tasks]
        for running_task in running_tasks:
            result_list.append(running_task.result())

    return result_list
