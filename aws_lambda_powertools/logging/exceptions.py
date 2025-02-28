class InvalidLoggerSamplingRateError(Exception):
    """
    Logger configured with Invalid Sampling value
    """

    pass


class OrphanedChildLoggerError(Exception):
    """
    Orphaned Child logger exception
    """

    pass
