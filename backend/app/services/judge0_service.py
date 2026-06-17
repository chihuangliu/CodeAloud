import os
import httpx
from ..models.session import ExecutionResult

JUDGE0_URL = os.environ.get("JUDGE0_URL", "http://judge0:2358")

LANGUAGE_IDS = {
    "python": 71,
    "javascript": 63,
    "java": 62,
    "cpp": 54,
}


async def execute(code: str, language: str = "python", stdin: str = "") -> ExecutionResult:
    language_id = LANGUAGE_IDS.get(language, LANGUAGE_IDS["python"])
    payload = {
        "source_code": code,
        "language_id": language_id,
        "stdin": stdin,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{JUDGE0_URL}/submissions",
            json=payload,
            params={"wait": "true", "base64_encoded": "false"},
        )
        resp.raise_for_status()
        data = resp.json()

    return ExecutionResult(
        stdout=data.get("stdout") or "",
        stderr=data.get("stderr") or "",
        status=data.get("status", {}).get("description", "Unknown"),
        time=data.get("time"),
    )
