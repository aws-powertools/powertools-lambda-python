from abc import ABC, abstractmethod
from uuid import uuid4

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


class MainAbstractClass(ABC):
    @abstractmethod
    def get_all(self):
        raise NotImplementedError


class Comments(MainAbstractClass):
    @tracer.capture_method
    def get_all(self):
        return [{"id": f"{uuid4()}", "completed": False} for _ in range(5)]


class Todos(MainAbstractClass):
    @tracer.capture_method
    def get_all(self):
        return [{"id": f"{uuid4()}", "completed": False} for _ in range(5)]


def lambda_handler(event: dict, context: LambdaContext):
    # Maintenance: create a public method to set these explicitly
    tracer.service = event["service"]

    todos = Todos()
    comments = Comments()

    return {"todos": todos.get_all(), "comments": comments.get_all()}
