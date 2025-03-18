import pytest

from aws_lambda_powertools.logging.buffer.cache import LoggerBufferCache


def test_initialization():

    # GIVEN a new instance of LoggerBufferCache
    logger_cache = LoggerBufferCache(1000)

    # THEN cache should have correct initial state
    assert logger_cache.max_size_bytes == 1000
    assert logger_cache.cache == {}


def test_add_single_item():
    # GIVEN a new instance of LoggerBufferCache with 1024 bytes
    logger_cache = LoggerBufferCache(1024)

    # WHEN a single item is added
    logger_cache.add("key1", "test_item")

    # THEN item is stored correctly with proper size tracking
    assert len(logger_cache.get("key1")) == 1
    assert logger_cache.get("key1")[0] == "test_item"
    assert logger_cache.get_current_size("key1") == len("test_item")


def test_add_multiple_items_same_key():
    # GIVEN a new instance of LoggerBufferCache with 1024 bytes
    logger_cache = LoggerBufferCache(1024)

    # WHEN multiple items are added to the same key
    logger_cache.add("key1", "item1")
    logger_cache.add("key1", "item2")

    # THEN items are stored sequentially
    assert len(logger_cache.get("key1")) == 2
    assert logger_cache.get("key1") == ["item1", "item2"]
    assert logger_cache.has_items_evicted("key1") is False


def test_cache_size_limit_single_key():
    # GIVEN a new instance of LoggerBufferCache with small cache size
    logger_cache = LoggerBufferCache(10)

    # WHEN multiple items are added
    logger_cache.add("key1", "long_item1")
    logger_cache.add("key1", "long_item2")
    logger_cache.add("key1", "long_item3")

    # THEN cache maintains size limit for a single key
    assert len(logger_cache.get("key1")) > 0
    assert logger_cache.get_current_size("key1") <= 10
    assert logger_cache.has_items_evicted("key1") is True


def test_item_larger_than_cache():
    # GIVEN a new instance of LoggerBufferCache with small cache size
    logger_cache = LoggerBufferCache(5)

    # WHEN an item larger than cache is added
    with pytest.raises(BufferError):
        # THEN a warning is raised
        logger_cache.add("key1", "very_long_item")

    # THEN the key is not added
    assert "key1" not in logger_cache.cache


def test_get_existing_key():
    # GIVEN a new instance of LoggerBufferCache with 1024 bytes
    logger_cache = LoggerBufferCache(1024)

    # WHEN we add keys
    logger_cache.add("key1", "item1")
    logger_cache.add("key1", "item2")

    # THEN all items are retrieved
    assert logger_cache.get("key1") == ["item1", "item2"]


def test_get_non_existing_key():
    # GIVEN a new instance of LoggerBufferCache with 1024 bytes
    logger_cache = LoggerBufferCache(1000)

    # WHEN getting items for a non-existing key
    retrieved = logger_cache.get("non_existing")

    # THEN an empty list is returned
    assert retrieved == []


def test_clear_all():
    # GIVEN a new instance of LoggerBufferCache with 1024 bytes
    logger_cache = LoggerBufferCache(1024)

    # WHEN we add multiple keys
    logger_cache.add("key1", "item1")
    logger_cache.add("key2", "item2")

    # WHEN clearing all keys
    logger_cache.clear()

    # THEN cache becomes empty
    assert logger_cache.cache == {}


def test_clear_specific_key():
    # GIVEN a new instance of LoggerBufferCache with 1024 bytes
    logger_cache = LoggerBufferCache(1024)

    # WHEN we add multiple keys
    logger_cache.add("key1", "item1")
    logger_cache.add("key2", "item2")

    # WHEN we remove a specific key
    logger_cache.clear("key1")

    # THEN only that key is removed
    assert "key1" not in logger_cache.cache
    assert "key2" in logger_cache.cache
    assert logger_cache.get("key1") == []


def test_multiple_keys_with_size_limits():
    # GIVEN a new instance of LoggerBufferCache with 20 bytes
    logger_cache = LoggerBufferCache(20)

    # WHEN adding items to multiple keys
    logger_cache.add("key1", "item1")
    logger_cache.add("key1", "item2")
    logger_cache.add("key2", "long_item")

    # THEN total size remains within limit
    assert len(logger_cache.get("key1")) > 0
    assert len(logger_cache.get("key2")) > 0
    assert logger_cache.get_current_size("key1") + logger_cache.get_current_size("key2") <= 20


def test_add_different_types():
    # GIVEN a new instance of LoggerBufferCache with 1024 bytes
    logger_cache = LoggerBufferCache(1024)

    # WHEN adding items of different types
    logger_cache.add("key1", 123)
    logger_cache.add("key1", [1, 2, 3])
    logger_cache.add("key1", {"a": 1})

    # THEN items are stored successfully
    retrieved = logger_cache.get("key1")
    assert len(retrieved) == 3


def test_cache_size_tracking():
    # GIVEN a new instance of LoggerBufferCache with 30 bytes
    logger_cache = LoggerBufferCache(30)

    # WHEN adding items
    logger_cache.add("key1", "small")
    logger_cache.add("key1", "another_item")

    # THEN current size is tracked correctly
    assert logger_cache.get_current_size("key1") == len("small") + len("another_item")
    assert logger_cache.get_current_size("key1") <= 30
