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


class InvalidBufferItem(Exception):
    """
    Raised when a buffer item exceeds the maximum allowed buffer size.
    """

    pass
