from pydantic import BaseModel


class TestCase(BaseModel):
    input: str
    output: str


class Question(BaseModel):
    id: str
    title: str
    difficulty: str
    tags: list[str]
    description: str
    test_cases: list[TestCase]
    hints: list[str]
    follow_ups: list[str]
    companies: list[str]
