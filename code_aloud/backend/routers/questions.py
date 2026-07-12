import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from ..models.question import Question

router = APIRouter(prefix="/questions", tags=["questions"])

_QUESTIONS_PATH = Path(__file__).parent.parent / "data" / "questions.json"


def _load() -> list[Question]:
    return [Question(**q) for q in json.loads(_QUESTIONS_PATH.read_text())]


@router.get("", response_model=list[Question])
async def list_questions(
    difficulty: str | None = None,
    tag: str | None = None,
):
    questions = _load()
    if difficulty:
        questions = [q for q in questions if q.difficulty == difficulty]
    if tag:
        questions = [q for q in questions if tag in q.tags]
    return questions


@router.get("/{question_id}", response_model=Question)
async def get_question(question_id: str):
    for q in _load():
        if q.id == question_id:
            return q
    raise HTTPException(status_code=404, detail="Question not found")
