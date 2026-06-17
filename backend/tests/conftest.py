import os
import pytest
from fastapi.testclient import TestClient

# Set env vars before app import so services initialise correctly
os.environ.setdefault("LLM_PROVIDER", "anthropic")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("LLM_MODEL", "claude-test")
os.environ.setdefault("JUDGE0_URL", "http://judge0-test:2358")
os.environ.setdefault("REDIS_URL", "redis://redis-test:6379")

from app.main import app  # noqa: E402 — must come after env setup
from app.models.question import Question, QuestionTestCase
from app.models.session import Session


@pytest.fixture
def client() -> TestClient:
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
def sample_question() -> Question:
    return Question(
        id="test-q1",
        title="Two Sum",
        difficulty="easy",
        tags=["hash-map", "array"],
        description="Given nums and target, return indices of two numbers that add up to target.",
        test_cases=[QuestionTestCase(input="nums=[2,7,11], target=9", output="[0,1]")],
        hints=["Try a hash map for O(1) lookup."],
        follow_ups=["What if the array were sorted?"],
        companies=["google"],
    )


@pytest.fixture
def sample_session(sample_question: Question) -> Session:
    s = Session(session_id="test-session-abc", question=sample_question)
    s.add_message("user", "Hello, I'm ready.")
    s.add_message("assistant", "Great! Here is your problem: Two Sum.")
    return s
