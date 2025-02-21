from __future__ import annotations

import warnings
from collections import deque
from typing import Any

from aws_lambda_powertools.warnings import PowertoolsUserWarning


class LoggerBufferCache:
    def __init__(self, max_size_bytes: int):
        """
        Initialize the LoggerBufferCache.

        Parameters
        ----------
        max_size_bytes : int
            Maximum size of the cache in bytes.
        """
        self.max_size_bytes: int = max_size_bytes
        self.cache: dict[str, deque] = {}
        self.current_size: dict[str, int] = {}
        self.has_evicted: bool = False

    def add(self, key: str, item: Any) -> None:
        """
        Add an item to the cache for a specific key.

        Parameters
        ----------
        key : str
            The key to store the item under.
        item : Any
            The item to be stored in the cache.

        Notes
        -----
        If the item size exceeds the maximum cache size, it will not be added.
        """
        item_size = len(str(item))

        if item_size > self.max_size_bytes:
            warnings.warn(
                message=f"Item size {item_size} bytes exceeds total cache size {self.max_size_bytes} bytes",
                category=PowertoolsUserWarning,
                stacklevel=2,
            )
            return

        if key not in self.cache:
            self.cache[key] = deque()
            self.current_size[key] = 0

        while self.current_size[key] + item_size > self.max_size_bytes and self.cache[key]:
            removed_item = self.cache[key].popleft()
            self.current_size[key] -= len(str(removed_item))
            self.has_evicted = True

        self.cache[key].append(item)
        self.current_size[key] += item_size

    def get(self, key: str) -> list:
        """
        Retrieve items for a specific key.

        Parameters
        ----------
        key : str
            The key to retrieve items for.

        Returns
        -------
        list
            List of items for the given key, or an empty list if the key doesn't exist.
        """
        return list(self.cache.get(key, deque()))

    def clear(self, key: str | None = None) -> None:
        """
        Clear the cache, either for a specific key or entirely.

        Parameters
        ----------
        key : str, optional
            The key to clear. If None, clears the entire cache.
        """
        if key:
            if key in self.cache:
                del self.cache[key]
                del self.current_size[key]
        else:
            self.cache.clear()
            self.current_size.clear()
