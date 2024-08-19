from collections import OrderedDict


class LRUDict(OrderedDict):
    """
    Cache implementation based on ordered dict with a maximum number of items. Last accessed item will be evicted
    first. Currently used by idempotency utility.
    """

    def __init__(self, max_items=1024, *args, **kwargs):
        self.max_items = max_items
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self.max_items:
            oldest = next(iter(self))
            del self[oldest]

    def get(self, key, *args, **kwargs):
        item = super().get(key, *args, **kwargs)
        if item:
            self.move_to_end(key=key)
        return item
