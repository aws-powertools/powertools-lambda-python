import random

import pytest

from aws_lambda_powertools.shared.cache_dict import LRUDict

MAX_CACHE_ITEMS = 50
PREFILL_CACHE_ITEMS = 50


@pytest.fixture
def populated_cache() -> LRUDict:
    cache_dict = LRUDict(max_items=MAX_CACHE_ITEMS, **{f"key_{i}": f"val_{i}" for i in range(0, PREFILL_CACHE_ITEMS)})
    return cache_dict


def test_cache_order_init(populated_cache: LRUDict):
    first_item = list(populated_cache._cache)[0]
    last_item = list(populated_cache._cache)[-1]

    assert first_item == "key_0"
    assert last_item == f"key_{MAX_CACHE_ITEMS - 1}"


def test_cache_order_getitem(populated_cache: LRUDict):
    random_value = random.randrange(0, MAX_CACHE_ITEMS)
    _ = populated_cache[f"key_{random_value}"]

    last_item = list(populated_cache._cache)[-1]

    assert last_item == f"key_{random_value}"


def test_cache_order_get(populated_cache: LRUDict):
    random_value = random.randrange(0, MAX_CACHE_ITEMS)
    _ = populated_cache.get(f"key_{random_value}")

    last_item = list(populated_cache._cache)[-1]

    assert last_item == f"key_{random_value}"


def test_cache_evict_over_max_items(populated_cache: LRUDict):
    assert "key_0" in populated_cache._cache
    assert len(populated_cache._cache) == MAX_CACHE_ITEMS
    populated_cache["new_item"] = "new_value"
    assert len(populated_cache._cache) == MAX_CACHE_ITEMS
    assert "key_0" not in populated_cache._cache
    assert "key_1" in populated_cache._cache


def test_setitem_moves_to_end(populated_cache: LRUDict):
    random_value = random.randrange(0, MAX_CACHE_ITEMS)
    populated_cache[f"key_{random_value}"] = f"new_val_{random_value}"
    last_item = list(populated_cache._cache)[-1]

    assert last_item == f"key_{random_value}"
    assert populated_cache[f"key_{random_value}"] == f"new_val_{random_value}"


def test_setitem_none_not_moved(populated_cache: LRUDict):
    populated_cache["value_is_none"] = None

    first_item = list(populated_cache._cache)[0]
    last_item = list(populated_cache._cache)[-1]

    assert first_item == "key_0"
    assert last_item == f"key_{MAX_CACHE_ITEMS - 1}"
