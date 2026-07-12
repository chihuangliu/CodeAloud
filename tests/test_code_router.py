from unittest.mock import AsyncMock, patch
from code_aloud.backend.models.session import ExecutionResult

GET_PATH = "code_aloud.backend.services.session_manager.get"
SAVE_PATH = "code_aloud.backend.services.session_manager.save"
JUDGE0_PATH = "code_aloud.backend.services.judge0_service.execute"


def mock_execution(stdout="6\n", stderr="", status="Accepted"):
    return AsyncMock(
        return_value=ExecutionResult(stdout=stdout, stderr=stderr, status=status)
    )


class TestExecuteCode:
    def test_returns_execution_result(self, client, sample_session):
        with (
            patch(GET_PATH, return_value=sample_session),
            patch(SAVE_PATH, new_callable=AsyncMock),
            patch(JUDGE0_PATH, mock_execution(stdout="6\n")),
        ):
            resp = client.post(
                "/code/execute",
                json={
                    "session_id": sample_session.session_id,
                    "code": "print(2 + 4)",
                    "language": "python",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["stdout"] == "6\n"
        assert data["status"] == "Accepted"

    def test_404_for_missing_session(self, client):
        with patch(GET_PATH, return_value=None):
            resp = client.post(
                "/code/execute",
                json={
                    "session_id": "ghost",
                    "code": "print(1)",
                },
            )
        assert resp.status_code == 404

    def test_snapshot_is_saved_to_session(self, client, sample_session):
        saved_sessions = []

        async def capture_save(session):
            saved_sessions.append(session)

        with (
            patch(GET_PATH, return_value=sample_session),
            patch(SAVE_PATH, side_effect=capture_save),
            patch(JUDGE0_PATH, mock_execution()),
        ):
            client.post(
                "/code/execute",
                json={
                    "session_id": sample_session.session_id,
                    "code": "def two_sum(): pass",
                },
            )

        assert len(saved_sessions) == 1
        assert "def two_sum()" in saved_sessions[0].code_snapshots[-1]

    def test_execution_result_stored_in_session(self, client, sample_session):
        saved_sessions = []

        async def capture_save(session):
            saved_sessions.append(session)

        with (
            patch(GET_PATH, return_value=sample_session),
            patch(SAVE_PATH, side_effect=capture_save),
            patch(JUDGE0_PATH, mock_execution(stdout="hello\n", status="Accepted")),
        ):
            client.post(
                "/code/execute",
                json={
                    "session_id": sample_session.session_id,
                    "code": "print('hello')",
                },
            )

        assert saved_sessions[0].last_execution.stdout == "hello\n"
        assert saved_sessions[0].last_execution.status == "Accepted"

    def test_stderr_returned_on_runtime_error(self, client, sample_session):
        with (
            patch(GET_PATH, return_value=sample_session),
            patch(SAVE_PATH, new_callable=AsyncMock),
            patch(
                JUDGE0_PATH,
                mock_execution(
                    stdout="", stderr="ZeroDivisionError", status="Runtime Error"
                ),
            ),
        ):
            resp = client.post(
                "/code/execute",
                json={
                    "session_id": sample_session.session_id,
                    "code": "print(1/0)",
                },
            )

        data = resp.json()
        assert "ZeroDivisionError" in data["stderr"]
        assert data["status"] == "Runtime Error"
