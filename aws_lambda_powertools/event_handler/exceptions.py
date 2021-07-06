from http import HTTPStatus


class ServiceError(Exception):
    """Service Error"""

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
    """Bad Request Error"""

    def __init__(self, msg: str):
        super().__init__(HTTPStatus.BAD_REQUEST.value, msg)


class UnauthorizedError(ServiceError):
    """Unauthorized Error"""

    def __init__(self, msg: str):
        super().__init__(HTTPStatus.UNAUTHORIZED.value, msg)


class NotFoundError(ServiceError):
    """Not Found Error"""

    def __init__(self, msg: str = "Not found"):
        super().__init__(HTTPStatus.NOT_FOUND.value, msg)


class InternalServerError(ServiceError):
    """Internal Server Error"""

    def __init__(self, message: str):
        super().__init__(HTTPStatus.INTERNAL_SERVER_ERROR.value, message)
