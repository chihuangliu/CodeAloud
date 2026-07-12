"""Join states.jsonl (execution signals) with hints.json (teacher labels) into
chat-format JSONL for finetuning (QLoRA / MLX both consume this shape), then
split into train/valid/test.

    python -m code_aloud.fine_tune.data.build_dataset
        ->   code_aloud/fine_tune/data/dataset/{train,valid,test}.jsonl
"""

import json
import random
from pathlib import Path

DATA = Path(__file__).resolve().parent  # code_aloud/fine_tune/data/
ROOT = DATA.parents[1]                   # code_aloud/
QUESTIONS = {
    q["id"]: q for q in json.load(open(ROOT / "backend" / "data" / "questions.json"))
}
HINTS = {
    k: v for k, v in json.load(open(DATA / "hints.json")).items() if not k.startswith("_")
}

# The slim hint-only system prompt the small model is trained under (distilled
# from the app's _IDENTITY). Style rules match code_aloud/fine_tune/data/hints.json.
SYSTEM = (
    "You are Alex, a coding interviewer. Given the problem, the candidate's "
    "current code, and its execution result, reply with ONE short guiding hint "
    "(1-3 sentences). Rules: never reveal the answer or write solution code; "
    "never quote test cases, expected outputs, "
    "or the traceback (the candidate cannot see those); reference only the "
    "candidate's own code and the problem statement. If no code has been written, "
    "just say so."
)


def render_user(state: dict) -> str:
    q = QUESTIONS[state["question_id"]]
    tests = "\n".join(f"  {tc['input']} -> {tc['output']}" for tc in q["test_cases"])
    ex = state["execution"]
    parts = [
        f"Problem: {q['title']} ({q['difficulty']})",
        q["description"],
        "Test cases:",
        tests,
        "",
        "Candidate's current code:",
        "```python",
        state["code"].rstrip(),
        "```",
        f"Execution: status={ex['status']}, passed={ex['passed_count']}/{ex['total_count']}",
    ]
    if ex["stdout"].strip():
        parts.append(f"stdout: {ex['stdout'].strip()!r}")
    if ex["stderr"].strip():
        parts.append(f"stderr: {ex['stderr'].strip()!r}")
    return "\n".join(parts)


def main() -> None:
    states = [json.loads(line) for line in open(DATA / "states.jsonl")]
    records, missing = [], []
    for s in states:
        key = f"{s['question_id']}::{s['label']}"
        hint = HINTS.get(key)
        if not hint:
            missing.append(key)
            continue
        records.append(
            (
                s["question_id"],
                {
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": render_user(s)},
                        {"role": "assistant", "content": hint},
                    ]
                },
            )
        )
    if missing:
        print("WARNING: no hint for", missing)

    # Held-out-by-question split: whole questions go to test/valid so the model
    # is evaluated on questions it never saw in training (generalization), not
    # just unseen states of a question it trained on.
    random.seed(0)
    qids = sorted({qid for qid, _ in records})
    random.shuffle(qids)
    n_test_q = max(1, round(len(qids) * 0.15))
    n_val_q = max(1, round(len(qids) * 0.10))
    test_q = set(qids[:n_test_q])
    val_q = set(qids[n_test_q : n_test_q + n_val_q])

    splits = {"train": [], "valid": [], "test": []}
    for qid, rec in records:
        if qid in test_q:
            splits["test"].append(rec)
        elif qid in val_q:
            splits["valid"].append(rec)
        else:
            splits["train"].append(rec)

    out = DATA / "dataset"
    out.mkdir(exist_ok=True)
    for name, rows in splits.items():
        with open(out / f"{name}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print(f"{name}: {len(rows)} records")
    print(f"held-out test questions:  {sorted(test_q)}")
    print(f"held-out valid questions: {sorted(val_q)}")
    print(f"total {len(records)} records -> {out}")


if __name__ == "__main__":
    main()
