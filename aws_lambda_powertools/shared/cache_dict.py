from collections import OrderedDict


class LRUDict:
    """
    Cache implementation based on ordered dict with a maximum number of items. Last accessed item will be evicted
    first, unless the item is None which will be evicted first. Currently used only by idempotency utility.
    """

    def __init__(self, max_items=1024, *args, **kwargs):
        self.max_items = max_items
        self._cache = OrderedDict(*args, **kwargs)

    def __getitem__(self, key: str):
        value = self._cache.__getitem__(key)
        if value:
            self._cache.move_to_end(key)
        return value

    def __setitem__(self, key: str, value):
        self._cache.__setitem__(key, value)
        if key in self._cache:
            self._cache.move_to_end(key, last=value is not None)
        if len(self._cache) > self.max_items:
            oldest = next(iter(self._cache))
            del self._cache[oldest]

    def get(self, key: str):
        value = self._cache.get(key)
        if value:
            self._cache.move_to_end(key)
        return value
