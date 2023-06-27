from abc import ABC, abstractmethod


class BaseConnectionSync(ABC):
    @abstractmethod
    def _init_connection(self):
        raise NotImplementedError()  # pragma: no cover
