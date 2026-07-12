import json
from unittest.mock import AsyncMock, patch
from code_aloud.backend.services import session_manager


def make_mock_redis(get_return=None):
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=get_return)
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()
    return mock_redis


class TestSessionManager:
    async def test_get_returns_none_when_missing(self):
        mock_redis = make_mock_redis(get_return=None)
        with patch("code_aloud.backend.services.session_manager.get_redis", return_value=mock_redis):
            result = await session_manager.get("nonexistent")
        assert result is None

    async def test_get_deserialises_session(self, sample_session):
        json_data = sample_session.model_dump_json()
        mock_redis = make_mock_redis(get_return=json_data)
        with patch("code_aloud.backend.services.session_manager.get_redis", return_value=mock_redis):
            result = await session_manager.get(sample_session.session_id)
        assert result is not None
        assert result.session_id == sample_session.session_id
        assert result.question.title == "Two Sum"

    async def test_save_serialises_and_sets_ttl(self, sample_session):
        mock_redis = make_mock_redis()
        with patch("code_aloud.backend.services.session_manager.get_redis", return_value=mock_redis):
            await session_manager.save(sample_session)

        call_args = mock_redis.set.call_args
        key, value = call_args.args
        assert key == f"session:{sample_session.session_id}"
        parsed = json.loads(value)
        assert parsed["session_id"] == sample_session.session_id
        assert call_args.kwargs.get("ex") == session_manager.SESSION_TTL

    async def test_save_key_uses_prefix(self, sample_session):
        mock_redis = make_mock_redis()
        with patch("code_aloud.backend.services.session_manager.get_redis", return_value=mock_redis):
            await session_manager.save(sample_session)
        key = mock_redis.set.call_args.args[0]
        assert key.startswith("session:")

    async def test_delete_removes_key(self, sample_session):
        mock_redis = make_mock_redis()
        with patch("code_aloud.backend.services.session_manager.get_redis", return_value=mock_redis):
            await session_manager.delete(sample_session.session_id)
        mock_redis.delete.assert_called_once_with(
            f"session:{sample_session.session_id}"
        )
