import hashlib
import json
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

import redis.asyncio as redis

from app.utils.logger import get_logger
from app.config.settings import settings

logger = get_logger()


class RedisManager:
    """
    Thin async wrapper around Redis for simple key/value storage
    (e.g. caching tool results, session metadata, intermediate state)
    and pub/sub (e.g. streaming agent chunks to the frontend).
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.client: Optional[redis.Redis] = None

    @asynccontextmanager
    async def _session(self):
        """Manages connect/close lifecycle for a single Redis operation."""
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            yield self.client
        finally:
            try:
                await self.client.aclose()
            except Exception as e:
                logger.error(f'[Redis Manager] Error closing client: {e}')
            finally:
                self.client = None

    def _serialize(self, value: Any) -> str:
        return value if isinstance(value, str) else json.dumps(value)

    def _build_key(self, key: str, serialized_value: str) -> str:
        """Composes a content-addressed key as key + hex digest of the value's content."""
        digest = hashlib.sha256(serialized_value.encode("utf-8")).hexdigest()[:16]
        return f"{key}:{digest}"

    async def get(self, key: str) -> Optional[Any]:
        """Fetch a value by its full key. Returns None if not found."""
        try:
            async with self._session() as client:
                value = await client.get(key)
                if value is None:
                    return None
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
        except Exception as e:
            logger.error(f'[Redis Manager] error in get(key={key}): {e}', exc_info=True)
            return None

    async def put(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        use_content_hash: bool = False,
    ) -> Optional[str]:
        """
        Stores value under `key`.

        use_content_hash=False (default): stores under `key` exactly as given.
        This is what arg-keyed caches want (e.g. tool_name + hashed query args) —
        the caller already knows the key, so a later get(key) works without
        needing to know a return value from put().

        use_content_hash=True: composes key as key + hex digest of the
        serialized value (original content-addressed behavior), useful for
        dedup-by-content rather than lookup-by-arguments. Returns the composed
        key on success so the caller can store it for later get/delete.
        """
        try:
            serialized = self._serialize(value)
            composed_key = self._build_key(key, serialized) if use_content_hash else key

            async with self._session() as client:
                if ttl:
                    await client.set(composed_key, serialized, ex=ttl)
                else:
                    await client.set(composed_key, serialized)

            return composed_key

        except Exception as e:
            logger.error(f'[Redis Manager] error in put(key={key}): {e}', exc_info=True)
            return None

    async def delete(self, key: str) -> bool:
        """Delete a key (pass the full/composed key). Returns True if removed."""
        try:
            async with self._session() as client:
                result = await client.delete(key)
                return result > 0
        except Exception as e:
            logger.error(f'[Redis Manager] error in delete(key={key}): {e}', exc_info=True)
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a glob-style pattern (e.g. 'web_search:*').
        Uses SCAN rather than KEYS to avoid blocking Redis on large keyspaces.
        Returns the number of keys deleted.
        """
        try:
            deleted = 0
            async with self._session() as client:
                async for k in client.scan_iter(match=pattern, count=500):
                    await client.delete(k)
                    deleted += 1
            return deleted
        except Exception as e:
            logger.error(f'[Redis Manager] error in delete_pattern(pattern={pattern}): {e}', exc_info=True)
            return 0

    async def publish_message(self, channel: str, streamdata: dict) -> bool:
        try:
            async with self._session() as client:
                await client.publish(channel, json.dumps(streamdata))
            return True
        except Exception as e:
            logger.error(f'[Redis Manager] error publishing to channel={channel}: {e}', exc_info=True)
            return False

    async def subscribe(self, channel: str) -> AsyncGenerator[dict, None]:
        """
        Subscribe to a channel and yield incoming envelope dicts as they arrive,
        e.g. {"type": "chunk", "data": "..."} or {"type": "completed"}.

        Automatically stops after yielding a {"type": "completed"} or
        {"type": "error"} message, so the caller's loop ends naturally
        without needing to check the type itself.

        Usage:
            async for envelope in redis_manager.subscribe(f"stream:{session_id}"):
                yield envelope
        """
        client = redis.from_url(self.redis_url, decode_responses=True)
        pubsub = client.pubsub()

        try:
            await pubsub.subscribe(channel)
            logger.info(f'[Redis Manager] Subscribed to channel={channel}')

            async for message in pubsub.listen():
                if message is None or message.get("type") != "message":
                    continue

                raw = message["data"]
                try:
                    envelope = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    envelope = {"type": "chunk", "data": raw}

                yield envelope

                if envelope.get("type") in ("completed", "error"):
                    break

        except Exception as e:
            logger.error(f'[Redis Manager] error in subscribe(channel={channel}): {e}', exc_info=True)
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.aclose()
            except Exception as e:
                logger.error(f'[Redis Manager] Error closing pubsub for channel={channel}: {e}')
            try:
                await client.aclose()
            except Exception as e:
                logger.error(f'[Redis Manager] Error closing subscribe client: {e}')
            logger.info(f'[Redis Manager] Unsubscribed from channel={channel}')