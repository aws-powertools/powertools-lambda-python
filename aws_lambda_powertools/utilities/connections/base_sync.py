from abc import ABC, abstractmethod


class BaseConnectionSync(ABC):
    @abstractmethod
    def init_connection(self):
        raise NotImplementedError()  # pragma: no cover
