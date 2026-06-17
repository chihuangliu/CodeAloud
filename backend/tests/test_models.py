import pytest
from app.models.session import Session, Message
from app.models.question import Question, QuestionTestCase


def make_session(n_messages: int) -> Session:
    q = Question(
        id="q1", title="T", difficulty="easy", tags=[], description="d",
        test_cases=[], hints=[], follow_ups=[], companies=[],
    )
    s = Session(session_id="sid", question=q)
    for i in range(n_messages):
        role = "user" if i % 2 == 0 else "assistant"
        s.add_message(role, f"message {i}")
    return s


class TestSessionMessages:
    def test_add_message_appends(self):
        s = make_session(0)
        s.add_message("user", "hello")
        assert len(s.messages) == 1
        assert s.messages[0].role == "user"
        assert s.messages[0].content == "hello"

    def test_to_api_messages_returns_dicts(self):
        s = make_session(3)
        msgs = s.to_api_messages()
        assert all(isinstance(m, dict) for m in msgs)
        assert all("role" in m and "content" in m for m in msgs)

    def test_to_api_messages_caps_at_20(self):
        s = make_session(30)
        msgs = s.to_api_messages()
        assert len(msgs) == 20

    def test_to_api_messages_keeps_most_recent(self):
        s = make_session(0)
        for i in range(25):
            s.add_message("user", f"msg {i}")
        msgs = s.to_api_messages()
        assert msgs[0]["content"] == "msg 5"
        assert msgs[-1]["content"] == "msg 24"

    def test_snapshot_code_appends(self):
        s = make_session(0)
        s.snapshot_code("def foo(): pass")
        s.snapshot_code("def foo(): return 1")
        assert len(s.code_snapshots) == 2
        assert s.code_snapshots[-1] == "def foo(): return 1"

    def test_hints_used_defaults_zero(self):
        s = make_session(0)
        assert s.hints_used == 0

    def test_session_serialise_round_trip(self, sample_session):
        json_str = sample_session.model_dump_json()
        restored = Session.model_validate_json(json_str)
        assert restored.session_id == sample_session.session_id
        assert restored.question.title == sample_session.question.title
        assert len(restored.messages) == len(sample_session.messages)
