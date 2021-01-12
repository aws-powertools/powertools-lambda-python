import logging


class SuppressFilter(logging.Filter):
    def __init__(self, logger):
        self.logger = logger

    def filter(self, record):  # noqa: A003
        """Suppress Log Records from registered logger

        It rejects log records from registered logger e.g. a child logger
        otherwise it honours log propagation from any log record
        created by loggers who don't have a handler.
        """
        logger = record.name
        return self.logger not in logger
