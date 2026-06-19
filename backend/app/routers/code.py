from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services import judge0_service, session_manager
from ..models.session import ExecutionResult

router = APIRouter(prefix="/code", tags=["code"])


class ExecuteRequest(BaseModel):
    session_id: str
    code: str
    language: str = "python"
    stdin: str = ""


@router.post("/execute", response_model=ExecutionResult)
async def execute_code(body: ExecuteRequest):
    session = await session_manager.get(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await judge0_service.execute(
        body.code, body.language, body.stdin, session.question
    )

    session.snapshot_code(body.code)
    session.last_execution = result
    await session_manager.save(session)

    return result
