import asyncio
import os
import time
import httpx
from ..models.session import ExecutionResult, TestCaseResult
from ..models.question import Question
from .code_harness import build_test_code, build_class_test_code, outputs_match

LANGUAGE_IDS = {
    "python": 71,
    "javascript": 63,
    "java": 62,
    "cpp": 54,
}

LANGUAGE_COMMANDS = {
    "python": ["python3", "-c"],
    "javascript": ["node", "-e"],
}


async def execute(
    code: str,
    language: str = "python",
    stdin: str = "",
    question: Question | None = None,
) -> ExecutionResult:
    runner = os.environ.get("CODE_RUNNER", "local")
    run = _execute_judge0 if runner == "judge0" else _execute_local

    if not question or not question.test_cases:
        return await run(code, language, stdin)

    results: list[TestCaseResult] = []
    first_stdout = ""
    first_stderr = ""
    first_status = "Accepted"
    first_time = None

    for i, tc in enumerate(question.test_cases):
        if question.function_name:
            harness = build_test_code(
                code,
                tc.input,
                question.function_name,
                question.params,
                question.return_type,
            )
        else:
            harness = build_class_test_code(code, tc.input)

        res = await run(harness, language, stdin)
        actual = res.stdout.strip()
        expected = tc.output.strip()
        passed = outputs_match(actual, expected)
        results.append(
            TestCaseResult(
                input=tc.input, expected=expected, actual=actual, passed=passed
            )
        )
        if i == 0:
            first_stdout = res.stdout
            first_stderr = res.stderr
            first_status = res.status
            first_time = res.time

    passed_count = sum(r.passed for r in results)
    return ExecutionResult(
        stdout=first_stdout,
        stderr=first_stderr,
        status="Accepted" if passed_count == len(results) else first_status,
        time=first_time,
        test_case_results=results,
        passed_count=passed_count,
        total_count=len(results),
    )


async def _execute_local(
    code: str, language: str = "python", stdin: str = ""
) -> ExecutionResult:
    cmd = LANGUAGE_COMMANDS.get(language)
    if not cmd:
        return ExecutionResult(
            stdout="", stderr=f"Unsupported language: {language}", status="Error"
        )
    start = time.monotonic()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            code,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(stdin.encode() if stdin else None), timeout=10.0
        )
        elapsed = f"{time.monotonic() - start:.3f}"
        status = "Accepted" if proc.returncode == 0 else "Runtime Error"
        return ExecutionResult(
            stdout=stdout_bytes.decode(errors="replace"),
            stderr=stderr_bytes.decode(errors="replace"),
            status=status,
            time=elapsed,
        )
    except asyncio.TimeoutError:
        proc.kill()
        return ExecutionResult(
            stdout="", stderr="", status="Time Limit Exceeded", time="10.0"
        )


async def _execute_judge0(
    code: str, language: str = "python", stdin: str = ""
) -> ExecutionResult:
    judge0_url = os.environ.get("JUDGE0_URL", "http://judge0:2358")
    language_id = LANGUAGE_IDS.get(language, LANGUAGE_IDS["python"])
    payload = {
        "source_code": code,
        "language_id": language_id,
        "stdin": stdin,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{judge0_url}/submissions",
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
