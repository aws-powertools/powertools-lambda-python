"""
Data Class for idempotency records.
"""

from __future__ import annotations

import datetime
import json
import logging
from types import MappingProxyType

logger = logging.getLogger(__name__)

STATUS_CONSTANTS = MappingProxyType({"INPROGRESS": "INPROGRESS", "COMPLETED": "COMPLETED", "EXPIRED": "EXPIRED"})


class DataRecord:
    """
    Data Class for idempotency records.
    """

    def __init__(
        self,
        idempotency_key: str,
        status: str = "",
        expiry_timestamp: int | None = None,
        in_progress_expiry_timestamp: int | None = None,
        response_data: str = "",
        payload_hash: str = "",
    ) -> None:
        """

        Parameters
        ----------
        idempotency_key: str
            hashed representation of the idempotent data
        status: str, optional
            status of the idempotent record
        expiry_timestamp: int, optional
            time before the record should expire, in seconds
        in_progress_expiry_timestamp: int, optional
            time before the record should expire while in the INPROGRESS state, in seconds
        payload_hash: str, optional
            hashed representation of payload
        response_data: str, optional
            response data from previous executions using the record
        """
        self.idempotency_key = idempotency_key
        self.payload_hash = payload_hash
        self.expiry_timestamp = expiry_timestamp
        self.in_progress_expiry_timestamp = in_progress_expiry_timestamp
        self._status = status
        self.response_data = response_data

    @property
    def is_expired(self) -> bool:
        """
        Check if data record is expired

        Returns
        -------
        bool
            Whether the record is currently expired or not
        """
        return bool(self.expiry_timestamp and int(datetime.datetime.now().timestamp()) > self.expiry_timestamp)

    @property
    def status(self) -> str:
        """
        Get status of data record

        Returns
        -------
        str
        """
        if self.is_expired:
            return STATUS_CONSTANTS["EXPIRED"]
        if self._status in STATUS_CONSTANTS.values():
            return self._status

        from aws_lambda_powertools.utilities.idempotency.exceptions import IdempotencyInvalidStatusError

        raise IdempotencyInvalidStatusError(self._status)

    def response_json_as_dict(self) -> dict | None:
        """
        Get response data deserialized to python dict

        Returns
        -------
        dict | None
            previous response data deserialized
        """
        return json.loads(self.response_data) if self.response_data else None

    def get_expiration_datetime(self) -> datetime.datetime | None:
        """
        Converts the expiry timestamp to a datetime object.

        This method checks if an expiry timestamp exists and converts it to a
        datetime object. If no timestamp is present, it returns None.

        Returns:
        -------
        datetime.datetime | None
            A datetime object representing the expiration time, or None if no expiry timestamp is set.

        Note:
        ----
        The returned datetime object is timezone-naive and assumes the timestamp
        is in the system's local timezone. Lambda default timezone is UTC.
        """
        if self.expiry_timestamp:
            return datetime.datetime.fromtimestamp(int(self.expiry_timestamp))
        return None
