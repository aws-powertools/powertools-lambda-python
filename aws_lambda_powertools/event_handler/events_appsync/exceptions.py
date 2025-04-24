from __future__ import annotations


class UnauthorizedException(Exception):
    """
    Error to be thrown to communicate the subscription is unauthorized.

    When this error is raised, the client will receive a 40x error code
    and the subscription will be closed.

    Attributes:
        message (str): The error message describing the unauthorized access.
    """

    def __init__(self, message: str | None = None, *args, **kwargs):
        """
        Initialize the UnauthorizedException.

        Args:
            message (str): A descriptive error message.
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.
        """
        super().__init__(message, *args, **kwargs)
        self.name = "UnauthorizedException"
