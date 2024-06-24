class ResolverNotFoundError(Exception):
    """
    When a resolver is not found during a lookup.
    """


class InvalidBatchResponse(Exception):
    """
    When a batch response something different from a List
    """
