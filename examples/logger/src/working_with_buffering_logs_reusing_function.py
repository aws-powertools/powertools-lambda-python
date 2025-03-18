from working_with_buffering_logs_creating_instance import logger  # reusing same instance


def my_function():
    logger.debug("This will be buffered")
    # do stuff
