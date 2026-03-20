"""
Lambda Metadata Service exceptions
"""


class LambdaMetadataError(Exception):
    """Raised when the Lambda Metadata Endpoint is unavailable or returns an error."""

    def __init__(self, message: str, status_code: int = -1):
        self.status_code = status_code
        super().__init__(message)
