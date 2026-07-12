"""Run the authored candidate snapshots (snapshots.json) through codeAloud's own
harness and record the ExecutionResult — the "judge signal" the hint model reads.

Data lives in snapshots.json; this script only executes and records. Uses the
local runner (CODE_RUNNER=local, the app's default) so judge0 need not be up.

    python -m code_aloud.fine_tune.data.gen_snapshots   ->   states.jsonl
"""
import asyncio
import json
import os
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent                 # code_aloud/fine_tune/data/
ROOT = DATA.parents[1]                                 # code_aloud/

os.environ["CODE_RUNNER"] = "local"                    # judge0 optional; matches app default
os.environ["PYTHON_COLORS"] = "0"                      # child python: no ANSI-colored tracebacks

# imports after the env setup above (judge0_service reads CODE_RUNNER at import)
from code_aloud.backend.models.question import Question           # noqa: E402
from code_aloud.backend.services import judge0_service            # noqa: E402

QUESTIONS = {q["id"]: q for q in json.load(open(ROOT / "backend" / "data" / "questions.json"))}
SNAPSHOTS = json.load(open(DATA / "snapshots.json"))["snapshots"]

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(s: str) -> str:
    return _ANSI.sub("", s or "")


async def main() -> None:
    out = []
    for snap in SNAPSHOTS:
        q = Question(**QUESTIONS[snap["question_id"]])
        ex = await judge0_service.execute(snap["code"], "python", question=q)
        out.append(
            {
                "question_id": snap["question_id"],
                "label": snap["label"],
                "stage": snap.get("stage", ""),
                "code": snap["code"],
                "execution": {
                    "status": ex.status,
                    "passed_count": ex.passed_count,
                    "total_count": ex.total_count,
                    "stdout": strip_ansi(ex.stdout),
                    "stderr": strip_ansi(ex.stderr),
                },
            }
        )
        print(f"{snap['question_id']}::{snap['label']:<14} {ex.status:<14} {ex.passed_count}/{ex.total_count}")

    path = DATA / "states.jsonl"
    with open(path, "w") as f:
        for row in out:
            f.write(json.dumps(row) + "\n")
    print(f"\nwrote {len(out)} states -> {path}")


if __name__ == "__main__":
    asyncio.run(main())
