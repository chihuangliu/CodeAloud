import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


def make_llm_client(chunks: list[str]):
    """Return a mock LLMClient whose stream() yields the given chunks."""
    async def _stream(messages, system):
        for chunk in chunks:
            yield chunk

    mock = MagicMock()
    mock.stream = _stream
    return mock


def parse_sse(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        if line.startswith("data: "):
            raw = line[6:].strip()
            if raw:
                events.append(json.loads(raw))
    return events


SAVE_PATH = "app.services.session_manager.save"
GET_PATH = "app.services.session_manager.get"
LLM_PATH = "app.routers.interview.get_llm_client"


class TestStartInterview:
    def test_streams_greeting_text(self, client):
        mock_llm = make_llm_client(["Hello", "! Welcome."])
        with patch(LLM_PATH, return_value=mock_llm), \
             patch(SAVE_PATH, new_callable=AsyncMock):
            resp = client.post("/interview/start", json={"question_id": "lc-1"})

        assert resp.status_code == 200
        events = parse_sse(resp.text)
        text_events = [e for e in events if "text" in e]
        assert text_events[0]["text"] == "Hello"
        assert text_events[1]["text"] == "! Welcome."

    def test_done_event_contains_session_id(self, client):
        mock_llm = make_llm_client(["Hi"])
        with patch(LLM_PATH, return_value=mock_llm), \
             patch(SAVE_PATH, new_callable=AsyncMock):
            resp = client.post("/interview/start", json={"question_id": "lc-1"})

        events = parse_sse(resp.text)
        done_events = [e for e in events if e.get("done")]
        assert len(done_events) == 1
        assert "session_id" in done_events[0]

    def test_404_for_unknown_question(self, client):
        resp = client.post("/interview/start", json={"question_id": "not-a-real-id"})
        assert resp.status_code == 404


class TestSendMessage:
    def test_streams_response(self, client, sample_session):
        mock_llm = make_llm_client(["Sure,", " good approach."])
        with patch(LLM_PATH, return_value=mock_llm), \
             patch(GET_PATH, return_value=sample_session), \
             patch(SAVE_PATH, new_callable=AsyncMock):
            resp = client.post("/interview/message", json={
                "session_id": sample_session.session_id,
                "content": "I want to use a hash map.",
            })

        assert resp.status_code == 200
        events = parse_sse(resp.text)
        text_chunks = [e["text"] for e in events if "text" in e]
        assert "".join(text_chunks) == "Sure, good approach."

    def test_404_for_missing_session(self, client):
        with patch(GET_PATH, return_value=None):
            resp = client.post("/interview/message", json={
                "session_id": "ghost-session",
                "content": "hello",
            })
        assert resp.status_code == 404

    def test_inject_code_flag_appends_snapshot(self, client, sample_session):
        sample_session.snapshot_code("def solve(): pass")
        mock_llm = make_llm_client(["Looks good"])
        captured_messages = []

        async def capturing_stream(messages, system):
            captured_messages.extend(messages)
            yield "Looks good"

        mock_llm.stream = capturing_stream

        with patch(LLM_PATH, return_value=mock_llm), \
             patch(GET_PATH, return_value=sample_session), \
             patch(SAVE_PATH, new_callable=AsyncMock):
            client.post("/interview/message", json={
                "session_id": sample_session.session_id,
                "content": "I'm done",
                "inject_code": True,
            })

        last_user_msg = next(m for m in reversed(captured_messages) if m["role"] == "user")
        assert "def solve()" in last_user_msg["content"]


class TestEndInterview:
    def test_returns_eval_report_structure(self, client, sample_session):
        report_json = json.dumps({
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
            "communication_score": 7,
            "approach_score": 8,
            "improvements": ["Consider edge cases for empty array"],
            "follow_up_quality": "Good explanation of sorted-array approach",
        })
        mock_llm = make_llm_client([report_json])

        with patch(LLM_PATH, return_value=mock_llm), \
             patch(GET_PATH, return_value=sample_session), \
             patch("app.services.session_manager.delete", new_callable=AsyncMock):
            resp = client.post("/interview/end", json={
                "session_id": sample_session.session_id,
                "content": "end",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["time_complexity"] == "O(n)"
        assert data["communication_score"] == 7
        assert len(data["improvements"]) == 1

    def test_returns_fallback_on_malformed_llm_output(self, client, sample_session):
        mock_llm = make_llm_client(["not valid json at all {{{"])

        with patch(LLM_PATH, return_value=mock_llm), \
             patch(GET_PATH, return_value=sample_session), \
             patch("app.services.session_manager.delete", new_callable=AsyncMock):
            resp = client.post("/interview/end", json={
                "session_id": sample_session.session_id,
                "content": "end",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "time_complexity" in data  # fallback fields present
