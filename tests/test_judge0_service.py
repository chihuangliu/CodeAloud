import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from code_aloud.backend.services.judge0_service import execute, LANGUAGE_IDS


def make_mock_response(data: dict, status_code: int = 200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = data
    mock_resp.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "err", request=MagicMock(), response=mock_resp
        )
        if status_code >= 400
        else None
    )
    return mock_resp


def patch_httpx(response_data: dict, status_code: int = 200):
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(
        return_value=make_mock_response(response_data, status_code)
    )
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return patch(
        "code_aloud.backend.services.judge0_service.httpx.AsyncClient", return_value=cm
    ), mock_client


class TestLanguageIds:
    def test_python_id(self):
        assert LANGUAGE_IDS["python"] == 71

    def test_javascript_id(self):
        assert LANGUAGE_IDS["javascript"] == 63

    def test_java_id(self):
        assert LANGUAGE_IDS["java"] == 62

    def test_cpp_id(self):
        assert LANGUAGE_IDS["cpp"] == 54


@pytest.fixture(autouse=True)
def _use_judge0(monkeypatch):
    monkeypatch.setenv("CODE_RUNNER", "judge0")


class TestExecute:
    async def test_returns_stdout_and_status(self):
        response_data = {
            "stdout": "hello\n",
            "stderr": "",
            "status": {"description": "Accepted"},
            "time": "0.05",
        }
        ctx, mock_client = patch_httpx(response_data)
        with ctx:
            result = await execute("print('hello')", "python")

        assert result.stdout == "hello\n"
        assert result.stderr == ""
        assert result.status == "Accepted"
        assert result.time == "0.05"

    async def test_sends_correct_language_id(self):
        response_data = {
            "stdout": "",
            "stderr": "",
            "status": {"description": "Accepted"},
        }
        ctx, mock_client = patch_httpx(response_data)
        with ctx:
            await execute("code", "javascript")

        call_kwargs = mock_client.post.call_args
        assert call_kwargs.kwargs["json"]["language_id"] == LANGUAGE_IDS["javascript"]

    async def test_falls_back_to_python_for_unknown_language(self):
        response_data = {
            "stdout": "",
            "stderr": "",
            "status": {"description": "Accepted"},
        }
        ctx, mock_client = patch_httpx(response_data)
        with ctx:
            await execute("code", "ruby")

        assert (
            mock_client.post.call_args.kwargs["json"]["language_id"]
            == LANGUAGE_IDS["python"]
        )

    async def test_returns_stderr_on_error_output(self):
        response_data = {
            "stdout": "",
            "stderr": "NameError: name 'x' is not defined",
            "status": {"description": "Runtime Error"},
        }
        ctx, _ = patch_httpx(response_data)
        with ctx:
            result = await execute("print(x)", "python")

        assert "NameError" in result.stderr
        assert result.status == "Runtime Error"

    async def test_passes_stdin(self):
        response_data = {
            "stdout": "5\n",
            "stderr": "",
            "status": {"description": "Accepted"},
        }
        ctx, mock_client = patch_httpx(response_data)
        with ctx:
            await execute("n = int(input()); print(n)", "python", stdin="5")

        assert mock_client.post.call_args.kwargs["json"]["stdin"] == "5"

    async def test_raises_on_http_error(self):
        ctx, _ = patch_httpx({}, status_code=500)
        with ctx, pytest.raises(httpx.HTTPStatusError):
            await execute("code", "python")
