class _FrozenDict(dict):
    """
    A dictionary that can be used as a key in another dictionary.

    This is needed because the default dict implementation is not hashable.
    The only usage for this right now is to store dicts as part of the Router key.
    The implementation only takes into consideration the keys of the dictionary.
    """

    def __hash__(self):
        return hash(frozenset(self.keys()))
