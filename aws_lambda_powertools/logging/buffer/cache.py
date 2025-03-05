from __future__ import annotations

from collections import deque
from typing import Any


class KeyBufferCache:
    """
    A cache implementation for a single key with size tracking and eviction support.

    This class manages a buffer for a specific key, keeping track of the current size
    and providing methods to add, remove, and manage cached items. It supports automatic
    eviction tracking and size management.

    Attributes
    ----------
    cache : deque
        A double-ended queue storing the cached items.
    current_size : int
        The total size of all items currently in the cache.
    has_evicted : bool
        A flag indicating whether any items have been evicted from the cache.
    """

    def __init__(self):
        """
        Initialize a buffer cache for a specific key.
        """
        self.cache: deque = deque()
        self.current_size: int = 0
        self.has_evicted: bool = False

    def add(self, item: Any) -> None:
        """
        Add an item to the cache.

        Parameters
        ----------
        item : Any
            The item to be stored in the cache.
        """
        item_size = len(str(item))
        self.cache.append(item)
        self.current_size += item_size

    def remove_oldest(self) -> Any:
        """
        Remove and return the oldest item from the cache.

        Returns
        -------
        Any
            The removed item.
        """
        removed_item = self.cache.popleft()
        self.current_size -= len(str(removed_item))
        self.has_evicted = True
        return removed_item

    def get(self) -> list:
        """
        Retrieve items for this key.

        Returns
        -------
        list
            List of items in the cache.
        """
        return list(self.cache)

    def clear(self) -> None:
        """
        Clear the cache for this key.
        """
        self.cache.clear()
        self.current_size = 0
        self.has_evicted = False


class LoggerBufferCache:
    """
    A multi-key buffer cache with size-based eviction and management.

    This class provides a flexible caching mechanism that manages multiple keys,
    with each key having its own buffer cache. The total size of each key's cache
    is limited, and older items are automatically evicted when the size limit is reached.

    Key Features:
    - Multiple key support
    - Size-based eviction
    - Tracking of evicted items
    - Configurable maximum buffer size

    Example
    --------
    >>> buffer_cache = LoggerBufferCache(max_size_bytes=1000)
    >>> buffer_cache.add("logs", "First log message")
    >>> buffer_cache.add("debug", "Debug information")
    >>> buffer_cache.get("logs")
    ['First log message']
    >>> buffer_cache.get_current_size("logs")
    16
    """

    def __init__(self, max_size_bytes: int):
        """
        Initialize the LoggerBufferCache.

        Parameters
        ----------
        max_size_bytes : int
            Maximum size of the cache in bytes for each key.
        """
        self.max_size_bytes: int = max_size_bytes
        self.cache: dict[str, KeyBufferCache] = {}

    def add(self, key: str, item: Any) -> None:
        """
        Add an item to the cache for a specific key.

        Parameters
        ----------
        key : str
            The key to store the item under.
        item : Any
            The item to be stored in the cache.

        Returns
        -------
        bool
            True if item was added, False otherwise.
        """
        # Check if item is larger than entire buffer
        item_size = len(str(item))
        if item_size > self.max_size_bytes:
            raise BufferError("Cannot add item to the buffer")

        # Create the key's cache if it doesn't exist
        if key not in self.cache:
            self.cache[key] = KeyBufferCache()

        # Calculate the size after adding the new item
        new_total_size = self.cache[key].current_size + item_size

        # If adding the item would exceed max size, remove oldest items
        while new_total_size > self.max_size_bytes and self.cache[key].cache:
            self.cache[key].remove_oldest()
            new_total_size = self.cache[key].current_size + item_size

        self.cache[key].add(item)

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
        return [] if key not in self.cache else self.cache[key].get()

    def clear(self, key: str | None = None) -> None:
        """
        Clear the cache, either for a specific key or entirely.

        Parameters
        ----------
        key : Optional[str], optional
            The key to clear. If None, clears the entire cache.
        """
        if key:
            if key in self.cache:
                self.cache[key].clear()
                del self.cache[key]
        else:
            self.cache.clear()

    def has_items_evicted(self, key: str) -> bool:
        """
        Check if a specific key's cache has evicted items.

        Parameters
        ----------
        key : str
            The key to check for evicted items.

        Returns
        -------
        bool
            True if items have been evicted, False otherwise.
        """
        return False if key not in self.cache else self.cache[key].has_evicted

    def get_current_size(self, key: str) -> int | None:
        """
        Get the current size of the buffer for a specific key.

        Parameters
        ----------
        key : str
            The key to get the current size for.

        Returns
        -------
        int
            The current size of the buffer for the key.
            Returns 0 if the key does not exist.
        """
        return None if key not in self.cache else self.cache[key].current_size
