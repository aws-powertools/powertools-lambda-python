class ResolverNotFound(Exception):
    """
    When a resolver is not found during a lookup.
    """


class InconsistentPayload(Exception):
    """
    When a payload is inconsistent or violates expected structure.
    """
