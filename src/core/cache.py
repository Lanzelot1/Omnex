"""Redis caching utilities for authentication."""

import json
from typing import Optional, Any, Dict
from datetime import timedelta

import redis.asyncio as redis
from redis.exceptions import RedisError

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    """Redis cache manager for authentication data."""
    
    def __init__(self, redis_url: str = None):
        """Initialize Redis connection."""
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis: Optional[redis.Redis] = None
        
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS
            )
            await self._redis.ping()
            logger.info("Connected to Redis cache")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis cache")
            
    @property
    def redis(self) -> redis.Redis:
        """Get Redis connection."""
        if not self._redis:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._redis
        
    # API Key caching methods
    
    async def cache_api_key(
        self, 
        key_hash: str, 
        api_key_data: Dict[str, Any],
        ttl: int = None
    ) -> None:
        """Cache API key data."""
        if ttl is None:
            ttl = settings.REDIS_AUTH_CACHE_TTL
            
        cache_key = f"{settings.API_KEY_CACHE_PREFIX}{key_hash}"
        try:
            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(api_key_data)
            )
            logger.debug(f"Cached API key: {cache_key[:20]}...")
        except RedisError as e:
            logger.error(f"Failed to cache API key: {e}")
            # Don't raise - caching is not critical
            
    async def get_cached_api_key(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached API key data."""
        cache_key = f"{settings.API_KEY_CACHE_PREFIX}{key_hash}"
        try:
            data = await self.redis.get(cache_key)
            if data:
                logger.debug(f"Cache hit for API key: {cache_key[:20]}...")
                return json.loads(data)
            logger.debug(f"Cache miss for API key: {cache_key[:20]}...")
            return None
        except RedisError as e:
            logger.error(f"Failed to get cached API key: {e}")
            return None
            
    async def invalidate_api_key(self, key_hash: str) -> None:
        """Invalidate cached API key."""
        cache_key = f"{settings.API_KEY_CACHE_PREFIX}{key_hash}"
        try:
            await self.redis.delete(cache_key)
            logger.debug(f"Invalidated API key cache: {cache_key[:20]}...")
        except RedisError as e:
            logger.error(f"Failed to invalidate API key cache: {e}")
            
    # User caching methods
    
    async def cache_user(
        self,
        user_id: str,
        user_data: Dict[str, Any],
        ttl: int = None
    ) -> None:
        """Cache user data."""
        if ttl is None:
            ttl = settings.REDIS_AUTH_CACHE_TTL
            
        cache_key = f"{settings.USER_CACHE_PREFIX}{user_id}"
        try:
            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(user_data)
            )
            logger.debug(f"Cached user: {user_id}")
        except RedisError as e:
            logger.error(f"Failed to cache user: {e}")
            
    async def get_cached_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user data."""
        cache_key = f"{settings.USER_CACHE_PREFIX}{user_id}"
        try:
            data = await self.redis.get(cache_key)
            if data:
                logger.debug(f"Cache hit for user: {user_id}")
                return json.loads(data)
            logger.debug(f"Cache miss for user: {user_id}")
            return None
        except RedisError as e:
            logger.error(f"Failed to get cached user: {e}")
            return None
            
    async def invalidate_user(self, user_id: str) -> None:
        """Invalidate cached user data."""
        cache_key = f"{settings.USER_CACHE_PREFIX}{user_id}"
        try:
            await self.redis.delete(cache_key)
            logger.debug(f"Invalidated user cache: {user_id}")
        except RedisError as e:
            logger.error(f"Failed to invalidate user cache: {e}")
            
    # Token blacklist methods
    
    async def blacklist_token(self, token_jti: str, expires_in: int) -> None:
        """Add token to blacklist."""
        cache_key = f"{settings.TOKEN_BLACKLIST_PREFIX}{token_jti}"
        try:
            await self.redis.setex(
                cache_key,
                expires_in,
                "1"
            )
            logger.debug(f"Blacklisted token: {token_jti}")
        except RedisError as e:
            logger.error(f"Failed to blacklist token: {e}")
            raise  # Blacklisting is critical
            
    async def is_token_blacklisted(self, token_jti: str) -> bool:
        """Check if token is blacklisted."""
        cache_key = f"{settings.TOKEN_BLACKLIST_PREFIX}{token_jti}"
        try:
            exists = await self.redis.exists(cache_key)
            return bool(exists)
        except RedisError as e:
            logger.error(f"Failed to check token blacklist: {e}")
            # Fail closed - treat as blacklisted on error
            return True
            
    # Batch operations
    
    async def invalidate_user_sessions(self, user_id: str) -> None:
        """Invalidate all sessions for a user."""
        # Invalidate user cache
        await self.invalidate_user(user_id)
        
        # In a full implementation, we would also:
        # - Blacklist all active refresh tokens
        # - Invalidate all API keys (if needed)
        # - Send events to connected clients
        logger.info(f"Invalidated all sessions for user: {user_id}")


# Global cache instance
cache = RedisCache()


async def get_cache() -> RedisCache:
    """Get cache instance for dependency injection."""
    return cache