# -*- coding: utf-8 -*-

"""
Batch processing utilities
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable, List, MutableSequence, Tuple


class BaseProcessor(ABC):
    """
    Abstract class for batch processors.
    """

    @abstractmethod
    def _prepare(self):
        """
        Prepare context manager.
        """
        raise NotImplementedError()

    @abstractmethod
    def _clean(self):
        """
        Clear context manager.
        """
        raise NotImplementedError()

    @abstractmethod
    def _process_record(self, record: Any):
        """
        Process record with handler.
        """
        raise NotImplementedError()

    def process(self) -> List[Tuple]:
        """
        Call instance's handler for each record.
        """
        return [self._process_record(record) for record in self.records]

    def __enter__(self):
        self._prepare()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._clean()

    def __call__(self, records: Iterable[Any], handler: Callable):
        """
        Set instance attributes before execution

        Parameters
        ----------
        records: Iterable[Any]
            Iterable with objects to be processed.
        handler: Callable
            Callable to process "records" entries.
        """
        self.records = records
        self.handler = handler
        return self


class BasePartialProcessor(BaseProcessor):

    success_messages: MutableSequence = None
    fail_messages: MutableSequence = None

    def success_handler(self, record: Any, result: Any):
        """
        Success callback

        Returns
        -------
        tuple
            "success", record processing result and original record
        """
        entry = ("success", result, record)
        self.success_messages.append(record)
        return entry

    def failure_handler(self, record: Any, exception: Exception):
        """
        Failure callback

        Returns
        -------
        tuple
            "fail", exceptions args, original record
        """
        entry = ("fail", exception.args, record)
        self.fail_messages.append(record)
        return entry
