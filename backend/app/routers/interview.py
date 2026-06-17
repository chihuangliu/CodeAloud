import json
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ..models.session import Session
from ..services import session_manager, prompt_builder
from ..services.llm_client import get_llm_client
from .questions import _load as load_questions

router = APIRouter(prefix="/interview", tags=["interview"])


class StartRequest(BaseModel):
    question_id: str


class MessageRequest(BaseModel):
    session_id: str
    content: str
    inject_code: bool = False


class EvalReport(BaseModel):
    time_complexity: str
    space_complexity: str
    communication_score: int
    approach_score: int
    improvements: list[str]
    follow_up_quality: str | None = None


@router.post("/start")
async def start_interview(body: StartRequest):
    question = next((q for q in load_questions() if q.id == body.question_id), None)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    session = Session(session_id=str(uuid.uuid4()), question=question)
    session.add_message("user", "Hello, I'm ready to start the interview.")
    await session_manager.save(session)

    llm = get_llm_client()
    system = prompt_builder.build_system_prompt(session)

    async def event_stream():
        full_response = ""
        async for chunk in llm.stream(session.to_api_messages(), system):
            full_response += chunk
            yield f"data: {json.dumps({'text': chunk})}\n\n"

        session.add_message("assistant", full_response)
        await session_manager.save(session)
        yield f"data: {json.dumps({'done': True, 'session_id': session.session_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/message")
async def send_message(body: MessageRequest):
    session = await session_manager.get(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    content = body.content
    if body.inject_code and session.code_snapshots:
        content += (
            f"\n\n[My current code]\n```python\n{session.code_snapshots[-1]}\n```"
        )
        if session.last_execution:
            ex = session.last_execution
            content += f"\n[Execution result] status={ex.status}, output={ex.stdout!r}"

    session.add_message("user", content)
    await session_manager.save(session)

    llm = get_llm_client()
    system = prompt_builder.build_system_prompt(session)

    async def event_stream():
        full_response = ""
        async for chunk in llm.stream(session.to_api_messages(), system):
            full_response += chunk
            yield f"data: {json.dumps({'text': chunk})}\n\n"

        session.add_message("assistant", full_response)
        await session_manager.save(session)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/end", response_model=EvalReport)
async def end_interview(body: MessageRequest):
    session = await session_manager.get(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    eval_prompt = f"""The coding interview for "{session.question.title}" has ended.
Review the conversation and return a JSON object with these exact keys:
- time_complexity: string (e.g. "O(n)")
- space_complexity: string (e.g. "O(1)")
- communication_score: integer 1-10
- approach_score: integer 1-10
- improvements: list of 2-3 specific improvement suggestions as strings
- follow_up_quality: string or null (how well they answered the follow-up, if asked)

Return ONLY valid JSON, no markdown."""

    llm = get_llm_client()
    messages = session.to_api_messages() + [{"role": "user", "content": eval_prompt}]

    result_text = ""
    async for chunk in llm.stream(
        messages, "You are a coding interview evaluator. Return only valid JSON."
    ):
        result_text += chunk

    await session_manager.delete(session.session_id)

    try:
        data = json.loads(result_text)
        return EvalReport(**data)
    except Exception:
        return EvalReport(
            time_complexity="N/A",
            space_complexity="N/A",
            communication_score=5,
            approach_score=5,
            improvements=["Could not parse evaluation."],
        )
