import random

import pytest

from aws_lambda_powertools.shared.cache_dict import LRUDict

MAX_CACHE_ITEMS = 50
PREFILL_CACHE_ITEMS = 50


@pytest.fixture
def populated_cache():
    cache_dict = LRUDict(max_items=MAX_CACHE_ITEMS, **{f"key_{i}": f"val_{i}" for i in range(0, PREFILL_CACHE_ITEMS)})
    return cache_dict


def test_cache_order_init(populated_cache):
    first_item = list(populated_cache)[0]
    last_item = list(populated_cache)[-1]

    assert first_item == "key_0"
    assert last_item == f"key_{MAX_CACHE_ITEMS - 1}"


def test_cache_order_getitem(populated_cache):
    random_value = random.randrange(0, MAX_CACHE_ITEMS)
    _ = populated_cache[f"key_{random_value}"]

    last_item = list(populated_cache)[-1]

    assert last_item == f"key_{random_value}"


def test_cache_order_get(populated_cache):
    random_value = random.randrange(0, MAX_CACHE_ITEMS)
    _ = populated_cache.get(f"key_{random_value}")

    last_item = list(populated_cache)[-1]

    assert last_item == f"key_{random_value}"


def test_cache_evict_over_max_items(populated_cache):
    assert "key_0" in populated_cache
    assert len(populated_cache) == MAX_CACHE_ITEMS
    populated_cache["new_item"] = "new_value"
    assert len(populated_cache) == MAX_CACHE_ITEMS
    assert "key_0" not in populated_cache
    assert "key_1" in populated_cache


def test_setitem_moves_to_end(populated_cache):
    random_value = random.randrange(0, MAX_CACHE_ITEMS)
    populated_cache[f"key_{random_value}"] = f"new_val_{random_value}"
    last_item = list(populated_cache)[-1]

    assert last_item == f"key_{random_value}"
    assert populated_cache[f"key_{random_value}"] == f"new_val_{random_value}"


def test_lru_pop_failing():
    cache = LRUDict()
    key = "test"
    cache[key] = "value"
    try:
        cache.pop(key, None)
        pytest.fail("GitHub #300: LRUDict pop bug has been fixed :)")
    except KeyError as e:
        assert e.args[0] == key


def test_lru_del():
    cache = LRUDict()
    key = "test"
    cache[key] = "value"
    assert len(cache) == 1
    if key in cache:
        del cache[key]
    assert key not in cache
    assert len(cache) == 0
