from http import HTTPStatus


class ServiceError(Exception):
    """Powertools class HTTP Service Error"""

    def __init__(self, status_code: int, msg: str):
        """
        Parameters
        ----------
        status_code: int
            Http status code
        msg: str
            Error message
        """
        self.status_code = status_code
        self.msg = msg


class BadRequestError(ServiceError):
    """Powertools class Bad Request Error (400)"""

    def __init__(self, msg: str):
        super().__init__(HTTPStatus.BAD_REQUEST, msg)


class UnauthorizedError(ServiceError):
    """Powertools class Unauthorized Error (401)"""

    def __init__(self, msg: str):
        super().__init__(HTTPStatus.UNAUTHORIZED, msg)


class ForbiddenError(ServiceError):
    """Powertools class Forbidden Error (403)"""

    def __init__(self, msg: str):
        super().__init__(HTTPStatus.FORBIDDEN, msg)


class NotFoundError(ServiceError):
    """Powertools class Not Found Error (404)"""

    def __init__(self, msg: str = "Not found"):
        super().__init__(HTTPStatus.NOT_FOUND, msg)


class RequestTimeoutError(ServiceError):
    """Powertools class Request Timeout Error (408)"""

    def __init__(self, msg: str):
        super().__init__(HTTPStatus.REQUEST_TIMEOUT, msg)


class RequestEntityTooLargeError(ServiceError):
    """Powertools class Request Entity Too Large Error (413)"""

    def __init__(self, msg: str):
        super().__init__(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, msg)


class InternalServerError(ServiceError):
    """Powertools class Internal Server Error (500)"""

    def __init__(self, message: str):
        super().__init__(HTTPStatus.INTERNAL_SERVER_ERROR, message)


class ServiceUnavailableError(ServiceError):
    """Powertools class Service Unavailable Error (503)"""

    def __init__(self, msg: str):
        super().__init__(HTTPStatus.SERVICE_UNAVAILABLE, msg)
