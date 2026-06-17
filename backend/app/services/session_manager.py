import os
import redis.asyncio as aioredis
from ..models.session import Session

SESSION_TTL = 60 * 60 * 2  # 2 hours


def _key(session_id: str) -> str:
    return f"session:{session_id}"


def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(os.environ["REDIS_URL"], decode_responses=True)


async def get(session_id: str) -> Session | None:
    async with _get_redis() as r:
        data = await r.get(_key(session_id))
    if data is None:
        return None
    return Session.model_validate_json(data)


async def save(session: Session) -> None:
    async with _get_redis() as r:
        await r.set(_key(session.session_id), session.model_dump_json(), ex=SESSION_TTL)


async def delete(session_id: str) -> None:
    async with _get_redis() as r:
        await r.delete(_key(session_id))
