import os
import redis.asyncio as aioredis
from ..models.session import Session

SESSION_TTL = 60 * 60 * 2  # 2 hours


def _key(session_id: str) -> str:
    return f"session:{session_id}"


_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    return _redis


async def get(session_id: str) -> Session | None:
    data = await get_redis().get(_key(session_id))
    if data is None:
        return None
    return Session.model_validate_json(data)


async def save(session: Session) -> None:
    await get_redis().set(
        _key(session.session_id), session.model_dump_json(), ex=SESSION_TTL
    )


async def delete(session_id: str) -> None:
    await get_redis().delete(_key(session_id))
