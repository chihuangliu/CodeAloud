from pydantic import BaseModel, Field
from typing import Literal
from .question import Question


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ExecutionResult(BaseModel):
    stdout: str
    stderr: str
    status: str
    time: str | None = None


class Session(BaseModel):
    session_id: str
    question: Question
    messages: list[Message] = Field(default_factory=list)
    elapsed_seconds: int = 0
    hints_used: int = 0
    code_snapshots: list[str] = Field(default_factory=list)
    last_execution: ExecutionResult | None = None

    def to_api_messages(self) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in self.messages[-20:]]

    def add_message(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))

    def snapshot_code(self, code: str) -> None:
        self.code_snapshots.append(code)
