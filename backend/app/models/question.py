from pydantic import BaseModel


class QuestionTestCase(BaseModel):
    input: str
    output: str


class Question(BaseModel):
    id: str
    title: str
    difficulty: str
    tags: list[str]
    description: str
    test_cases: list[QuestionTestCase]
    hints: list[str]
    follow_ups: list[str]
    companies: list[str]
