import logging


class SuppressFilter(logging.Filter):
    def __init__(self, logger):
        self.logger = logger

    def filter(self, record):  # noqa: A003
        """Suppress Log Records from registered logger"""
        if self.logger in record.name:
            return False
        return True
