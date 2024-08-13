from http import HTTPStatus


class ServiceError(Exception):
    """API Gateway and ALB HTTP Service Error"""

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
    """API Gateway and ALB Bad Request Error (400)"""

    def __init__(self, msg: str):
        super().__init__(HTTPStatus.BAD_REQUEST, msg)


class UnauthorizedError(ServiceError):
    """API Gateway and ALB Unauthorized Error (401)"""

    def __init__(self, msg: str):
        super().__init__(HTTPStatus.UNAUTHORIZED, msg)


class NotFoundError(ServiceError):
    """API Gateway and ALB Not Found Error (404)"""

    def __init__(self, msg: str = "Not found"):
        super().__init__(HTTPStatus.NOT_FOUND, msg)


class InternalServerError(ServiceError):
    """API Gateway and ALB Internal Server Error (500)"""

    def __init__(self, message: str):
        super().__init__(HTTPStatus.INTERNAL_SERVER_ERROR, message)
