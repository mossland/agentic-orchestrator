"""
Redis cache implementation for Agentic Orchestrator.

Provides caching, Pub/Sub, and real-time data support.
Falls back to in-memory cache when Redis is not available.
"""

import json
import os
from datetime import timedelta
from typing import Optional, Any, Dict, List, Callable
from dataclasses import dataclass
import threading
import time


class CacheKeys:
    """Cache key patterns."""

    # Signals
    SIGNALS_RECENT = "signals:recent:{hours}"
    SIGNALS_BY_SOURCE = "signals:source:{source}"
    SIGNALS_COUNT = "signals:count"

    # Trends
    TRENDS_LATEST = "trends:latest:{period}"
    TRENDS_BY_CATEGORY = "trends:category:{category}"

    # Ideas
    IDEAS_BY_STATUS = "ideas:status:{status}"
    IDEAS_COUNT = "ideas:count"

    # Debates
    DEBATE_SESSION = "debate:session:{session_id}"
    DEBATE_ACTIVE = "debate:active"

    # Budget
    BUDGET_TODAY = "budget:today"
    BUDGET_MONTH = "budget:month"

    # Agents
    AGENT_STATE = "agent:state:{agent_id}"
    AGENTS_ACTIVE = "agents:active"

    # System
    SYSTEM_STATUS = "system:status"
    SYSTEM_METRICS = "system:metrics"

    # Pub/Sub channels
    CHANNEL_SIGNALS = "channel:signals"
    CHANNEL_DEBATES = "channel:debates"
    CHANNEL_LOGS = "channel:logs"


@dataclass
class CacheConfig:
    """Cache configuration."""
    default_ttl: int = 300  # 5 minutes
    signals_ttl: int = 900  # 15 minutes
    trends_ttl: int = 3600  # 1 hour
    budget_ttl: int = 60  # 1 minute
    agent_ttl: int = 30  # 30 seconds


class InMemoryCache:
    """Simple in-memory cache fallback when Redis is not available."""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        self._lock = threading.Lock()
        self._pubsub_handlers: Dict[str, List[Callable]] = {}

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry is None or time.time() < expiry:
                    return value
                else:
                    del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        with self._lock:
            expiry = time.time() + ttl if ttl else None
            self._cache[key] = (value, expiry)
            return True

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def incr(self, key: str, amount: int = 1) -> int:
        with self._lock:
            current = self._cache.get(key, (0, None))[0]
            new_value = current + amount
            self._cache[key] = (new_value, None)
            return new_value

    def publish(self, channel: str, message: Any):
        """Publish to in-memory subscribers."""
        if channel in self._pubsub_handlers:
            for handler in self._pubsub_handlers[channel]:
                try:
                    handler(message)
                except Exception:
                    pass

    def subscribe(self, channel: str, handler: Callable):
        """Subscribe to a channel."""
        if channel not in self._pubsub_handlers:
            self._pubsub_handlers[channel] = []
        self._pubsub_handlers[channel].append(handler)

    def cleanup_expired(self):
        """Remove expired entries."""
        with self._lock:
            now = time.time()
            expired = [
                k for k, (_, exp) in self._cache.items()
                if exp is not None and now >= exp
            ]
            for key in expired:
                del self._cache[key]


class RedisCache:
    """
    Redis cache with fallback to in-memory.

    Features:
    - Key-value caching with TTL
    - Pub/Sub messaging
    - Counters
    - Graceful fallback to in-memory when Redis is unavailable
    """

    def __init__(self, url: Optional[str] = None, config: Optional[CacheConfig] = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.config = config or CacheConfig()
        self._redis = None
        self._fallback = InMemoryCache()
        self._use_fallback = False

        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            import redis
            self._redis = redis.from_url(
                self.url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self._redis.ping()
            self._use_fallback = False
        except Exception as e:
            print(f"Redis not available, using in-memory cache: {e}")
            self._use_fallback = True

    def _serialize(self, value: Any) -> str:
        """Serialize value to JSON."""
        return json.dumps(value, default=str)

    def _deserialize(self, value: str) -> Any:
        """Deserialize value from JSON."""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if self._use_fallback:
            return self._fallback.get(key)

        try:
            data = self._redis.get(key)
            if data:
                return self._deserialize(data)
            return None
        except Exception:
            self._use_fallback = True
            return self._fallback.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        ttl = ttl or self.config.default_ttl

        if self._use_fallback:
            return self._fallback.set(key, value, ttl)

        try:
            return bool(self._redis.setex(
                key,
                timedelta(seconds=ttl),
                self._serialize(value)
            ))
        except Exception:
            self._use_fallback = True
            return self._fallback.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if self._use_fallback:
            return self._fallback.delete(key)

        try:
            return bool(self._redis.delete(key))
        except Exception:
            self._use_fallback = True
            return self._fallback.delete(key)

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        if self._use_fallback:
            return self._fallback.exists(key)

        try:
            return bool(self._redis.exists(key))
        except Exception:
            self._use_fallback = True
            return self._fallback.exists(key)

    def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        if self._use_fallback:
            return self._fallback.incr(key, amount)

        try:
            return self._redis.incrby(key, amount)
        except Exception:
            self._use_fallback = True
            return self._fallback.incr(key, amount)

    def get_counter(self, key: str) -> int:
        """Get counter value."""
        value = self.get(key)
        return int(value) if value else 0

    # Pub/Sub methods
    def publish(self, channel: str, message: Any):
        """Publish message to channel."""
        if self._use_fallback:
            self._fallback.publish(channel, message)
            return

        try:
            self._redis.publish(channel, self._serialize(message))
        except Exception:
            self._fallback.publish(channel, message)

    def subscribe(self, channel: str, handler: Callable = None):
        """
        Subscribe to a channel.

        For Redis: Returns a pubsub object
        For fallback: Registers the handler
        """
        if self._use_fallback:
            if handler:
                self._fallback.subscribe(channel, handler)
            return None

        try:
            pubsub = self._redis.pubsub()
            pubsub.subscribe(channel)
            return pubsub
        except Exception:
            if handler:
                self._fallback.subscribe(channel, handler)
            return None

    # Hash operations
    def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field value."""
        if self._use_fallback:
            data = self._fallback.get(f"{name}:{key}")
            return data

        try:
            data = self._redis.hget(name, key)
            if data:
                return self._deserialize(data)
            return None
        except Exception:
            self._use_fallback = True
            return self._fallback.get(f"{name}:{key}")

    def hset(self, name: str, key: str, value: Any) -> bool:
        """Set hash field value."""
        if self._use_fallback:
            return self._fallback.set(f"{name}:{key}", value)

        try:
            return bool(self._redis.hset(name, key, self._serialize(value)))
        except Exception:
            self._use_fallback = True
            return self._fallback.set(f"{name}:{key}", value)

    def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields."""
        if self._use_fallback:
            # Not efficiently supported in fallback
            return {}

        try:
            data = self._redis.hgetall(name)
            return {k: self._deserialize(v) for k, v in data.items()}
        except Exception:
            return {}

    # List operations
    def lpush(self, key: str, *values: Any) -> int:
        """Push to list (left)."""
        if self._use_fallback:
            current = self._fallback.get(key) or []
            for v in values:
                current.insert(0, v)
            self._fallback.set(key, current)
            return len(current)

        try:
            return self._redis.lpush(key, *[self._serialize(v) for v in values])
        except Exception:
            current = self._fallback.get(key) or []
            for v in values:
                current.insert(0, v)
            self._fallback.set(key, current)
            return len(current)

    def lrange(self, key: str, start: int, end: int) -> List[Any]:
        """Get list range."""
        if self._use_fallback:
            current = self._fallback.get(key) or []
            if end == -1:
                return current[start:]
            return current[start:end + 1]

        try:
            data = self._redis.lrange(key, start, end)
            return [self._deserialize(v) for v in data]
        except Exception:
            current = self._fallback.get(key) or []
            if end == -1:
                return current[start:]
            return current[start:end + 1]

    def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to specified range."""
        if self._use_fallback:
            current = self._fallback.get(key) or []
            if end == -1:
                trimmed = current[start:]
            else:
                trimmed = current[start:end + 1]
            self._fallback.set(key, trimmed)
            return True

        try:
            return self._redis.ltrim(key, start, end)
        except Exception:
            return False

    # Utility methods
    def health_check(self) -> Dict[str, Any]:
        """Check cache health."""
        if self._use_fallback:
            return {
                "status": "fallback",
                "type": "in-memory",
                "message": "Using in-memory cache (Redis not available)"
            }

        try:
            self._redis.ping()
            info = self._redis.info("memory")
            return {
                "status": "healthy",
                "type": "redis",
                "used_memory": info.get("used_memory_human", "unknown")
            }
        except Exception as e:
            return {
                "status": "error",
                "type": "redis",
                "message": str(e)
            }

    def flush(self):
        """Clear all cache (use with caution!)."""
        if self._use_fallback:
            self._fallback._cache.clear()
            return

        try:
            self._redis.flushdb()
        except Exception:
            self._fallback._cache.clear()


# Global cache instance
_cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get or create the global cache instance."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache


def init_cache(url: Optional[str] = None, config: Optional[CacheConfig] = None) -> RedisCache:
    """Initialize the global cache instance."""
    global _cache
    _cache = RedisCache(url, config)
    return _cache
