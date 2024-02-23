class ResolverNotFoundError(Exception):
    """
    When a resolver is not found during a lookup.
    """


class InconsistentPayloadError(Exception):
    """
    When a payload is inconsistent or violates expected structure.
    """
