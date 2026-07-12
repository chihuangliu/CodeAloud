from pydantic import BaseModel, Field


class QuestionTestCase(BaseModel):
    input: str
    output: str


class QuestionParam(BaseModel):
    name: str
    type: str


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
    function_name: str | None = None
    params: list[QuestionParam] = Field(default_factory=list)
    return_type: str = ""
    starter_code: str = ""
