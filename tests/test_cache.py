"""Tests for SearchCache functionality."""

import asyncio

import pytest

from file_knowledge_mcp.search.cache import SearchCache
from file_knowledge_mcp.search.ugrep import SearchResult, UgrepEngine


# ============================================================================
# SearchCache Tests
# ============================================================================


@pytest.mark.asyncio
async def test_cache_basic_functionality():
    """Test basic cache get/set operations."""
    cache = SearchCache(max_size=10, ttl_seconds=60)

    # Initially empty
    result = await cache.get("test query", "/path", fuzzy=False)
    assert result is None

    # Set and get
    test_result = SearchResult(
        query="test query",
        matches=[],
        total_matches=0,
        truncated=False,
        searched_path="/path"
    )
    await cache.set("test query", "/path", test_result, fuzzy=False)

    cached = await cache.get("test query", "/path", fuzzy=False)
    assert cached is not None
    assert cached.query == "test query"


@pytest.mark.asyncio
async def test_cache_hit_counting():
    """Test that cache tracks hit counts."""
    cache = SearchCache(max_size=10, ttl_seconds=60)

    test_result = SearchResult(query="test", matches=[], total_matches=0, truncated=False, searched_path="/path")
    await cache.set("test", "/path", test_result)

    # Access multiple times
    await cache.get("test", "/path")
    await cache.get("test", "/path")
    await cache.get("test", "/path")

    stats = cache.stats
    assert stats["total_hits"] == 3


@pytest.mark.asyncio
async def test_cache_ttl_expiration():
    """Test that cache entries expire after TTL."""
    cache = SearchCache(max_size=10, ttl_seconds=1)  # 1 second TTL

    test_result = SearchResult(query="test", matches=[], total_matches=0, truncated=False, searched_path="/path")
    await cache.set("test", "/path", test_result)

    # Should be cached initially
    cached = await cache.get("test", "/path")
    assert cached is not None

    # Wait for expiration
    await asyncio.sleep(1.5)

    # Should be expired
    cached = await cache.get("test", "/path")
    assert cached is None


@pytest.mark.asyncio
async def test_cache_eviction():
    """Test that cache evicts oldest entry when at capacity."""
    cache = SearchCache(max_size=3, ttl_seconds=60)

    # Fill cache to capacity
    for i in range(3):
        result = SearchResult(query=f"query{i}", matches=[], total_matches=0, truncated=False, searched_path=f"/path{i}")
        await cache.set(f"query{i}", f"/path{i}", result)
        await asyncio.sleep(0.01)  # Ensure different timestamps

    assert cache.stats["entries"] == 3

    # Add one more, should evict oldest
    result = SearchResult(query="query3", matches=[], total_matches=0, truncated=False, searched_path="/path3")
    await cache.set("query3", "/path3", result)

    assert cache.stats["entries"] == 3

    # Oldest (query0) should be evicted
    assert await cache.get("query0", "/path0") is None
    assert await cache.get("query3", "/path3") is not None


@pytest.mark.asyncio
async def test_cache_key_generation():
    """Test that different parameters generate different cache keys."""
    cache = SearchCache(max_size=10, ttl_seconds=60)

    result1 = SearchResult(query="test", matches=[], total_matches=0, truncated=False, searched_path="/path1")
    result2 = SearchResult(query="test", matches=[], total_matches=0, truncated=False, searched_path="/path2")

    # Same query, different paths
    await cache.set("test", "/path1", result1)
    await cache.set("test", "/path2", result2)

    # Should be separate cache entries
    assert cache.stats["entries"] == 2

    # Same query and path, different kwargs
    await cache.set("test", "/path1", result1, fuzzy=True)
    assert cache.stats["entries"] == 3


@pytest.mark.asyncio
async def test_cache_clear():
    """Test cache clear functionality."""
    cache = SearchCache(max_size=10, ttl_seconds=60)

    # Add some entries
    for i in range(5):
        result = SearchResult(query=f"query{i}", matches=[], total_matches=0, truncated=False, searched_path=f"/path{i}")
        await cache.set(f"query{i}", f"/path{i}", result)

    assert cache.stats["entries"] == 5

    # Clear cache
    await cache.clear()

    assert cache.stats["entries"] == 0
    assert cache.stats["total_hits"] == 0


@pytest.mark.asyncio
async def test_cache_stats():
    """Test cache statistics."""
    cache = SearchCache(max_size=100, ttl_seconds=60)

    # Add entries
    for i in range(5):
        result = SearchResult(query=f"query{i}", matches=[], total_matches=0, truncated=False, searched_path=f"/path{i}")
        await cache.set(f"query{i}", f"/path{i}", result)

    # Access some entries
    await cache.get("query0", "/path0")
    await cache.get("query0", "/path0")
    await cache.get("query1", "/path1")

    stats = cache.stats
    assert stats["entries"] == 5
    assert stats["max_size"] == 100
    assert stats["total_hits"] == 3


@pytest.mark.asyncio
async def test_cache_integration_with_engine(rich_config, rich_knowledge_dir):
    """Test cache integration with UgrepEngine."""
    cache = SearchCache(max_size=10, ttl_seconds=60)
    engine = UgrepEngine(rich_config, cache=cache)

    # First search - cache miss
    result1 = await engine.search(
        query="movement",
        path=rich_knowledge_dir,
        recursive=True,
        context_lines=2,
        max_results=10,
    )

    assert cache.stats["entries"] == 1
    assert cache.stats["total_hits"] == 0

    # Second identical search - cache hit
    result2 = await engine.search(
        query="movement",
        path=rich_knowledge_dir,
        recursive=True,
        context_lines=2,
        max_results=10,
    )

    assert cache.stats["entries"] == 1
    assert cache.stats["total_hits"] == 1

    # Results should be identical
    assert result1.total_matches == result2.total_matches
