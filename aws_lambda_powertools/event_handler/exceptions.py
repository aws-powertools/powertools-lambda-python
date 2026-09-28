from __future__ import annotations

from http import HTTPStatus


class ResponseSizeExceededError(Exception):
    """The serialized Lambda response exceeds the integration's size limit."""

    def __init__(self, *, actual_size: int, max_size: int):
        """
        Parameters
        ----------
        actual_size: int
            Size of the complete serialized response in bytes.
        max_size: int
            Maximum allowed serialized response size in bytes.
        """
        self.actual_size = actual_size
        self.max_size = max_size
        super().__init__(
            f"Serialized response size ({actual_size} bytes) exceeds the maximum allowed size ({max_size} bytes)",
        )


class ServiceError(Exception):
    """Powertools class HTTP Service Error"""

    def __init__(self, status_code: int, msg: str | dict):
        """
        Parameters
        ----------
        status_code: int
            Http status code
        msg: str | dict
            Error message. Can be a string or a dictionary
        """
        self.status_code = status_code
        self.msg = msg


class BadRequestError(ServiceError):
    """Powertools class Bad Request Error (400)"""

    def __init__(self, msg: str | dict):
        """
        Parameters
        ----------
        msg : str | dict
            Error message. Can be a string or a dictionary.
        """
        super().__init__(HTTPStatus.BAD_REQUEST, msg)


class UnauthorizedError(ServiceError):
    """Powertools class Unauthorized Error (401)"""

    def __init__(self, msg: str | dict):
        """
        Parameters
        ----------
        msg : str | dict
            Error message. Can be a string or a dictionary.
        """
        super().__init__(HTTPStatus.UNAUTHORIZED, msg)


class ForbiddenError(ServiceError):
    """Powertools class Forbidden Error (403)"""

    def __init__(self, msg: str | dict):
        """
        Parameters
        ----------
        msg : str | dict
            Error message. Can be a string or a dictionary.
        """
        super().__init__(HTTPStatus.FORBIDDEN, msg)


class NotFoundError(ServiceError):
    """Powertools class Not Found Error (404)"""

    def __init__(self, msg: str | dict = "Not found"):
        """
        Parameters
        ----------
        msg : str | dict
            Error message. Can be a string or a dictionary.
        """
        super().__init__(HTTPStatus.NOT_FOUND, msg)


class RequestTimeoutError(ServiceError):
    """Powertools class Request Timeout Error (408)"""

    def __init__(self, msg: str | dict):
        """
        Parameters
        ----------
        msg : str | dict
            Error message. Can be a string or a dictionary.
        """
        super().__init__(HTTPStatus.REQUEST_TIMEOUT, msg)


class RequestEntityTooLargeError(ServiceError):
    """Powertools class Request Entity Too Large Error (413)"""

    def __init__(self, msg: str | dict):
        """
        Parameters
        ----------
        msg : str | dict
            Error message. Can be a string or a dictionary.
        """
        super().__init__(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, msg)


class InternalServerError(ServiceError):
    """Powertools class Internal Server Error (500)"""

    def __init__(self, message: str | dict):
        """
        Parameters
        ----------
        msg : str | dict
            Error message. Can be a string or a dictionary.
        """
        super().__init__(HTTPStatus.INTERNAL_SERVER_ERROR, message)


class ServiceUnavailableError(ServiceError):
    """Powertools class Service Unavailable Error (503)"""

    def __init__(self, msg: str | dict):
        """
        Parameters
        ----------
        msg : str | dict
            Error message. Can be a string or a dictionary.
        """
        super().__init__(HTTPStatus.SERVICE_UNAVAILABLE, msg)
