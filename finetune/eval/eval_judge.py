"""Evaluate hint quality on the held-out test questions.

Two layers:
  A. Deterministic regex gates (cheap, high-precision hard fails).
  B. LLM-as-judge semantic scoring (0-7) + complexity-conduct rule.

The judge is pluggable (JudgeBackend) so it runs on the current Claude Code
subscription for free, and swaps to the Anthropic API without touching the
rubric:

  # automated, on the Claude subscription (default), scoring teacher hints:
  python finetune/eval/eval_judge.py
  # score a model's predictions:
  python finetune/eval/eval_judge.py --predictions preds.jsonl
  # via API instead:
  python finetune/eval/eval_judge.py --backend api --model claude-opus-4-8

predictions.jsonl (optional): one object per line {"question_id","label","hint"}.
If absent, the teacher hint from hints.json is scored (baseline / self-check).

Backends (--backend):
  claude-cli (default): shells out to `claude -p` per item; automated, no API key,
                        draws on the Claude subscription; runs in any terminal.
  manual:               file handoff — writes to_judge.jsonl and stops; a Claude
                        Code agent must write judged.jsonl by hand, then rerun.
                        NOT automated (dead-ends in a plain terminal).
  api:                  Anthropic SDK (billed per token).
"""
import argparse
import json
import random
import re
from pathlib import Path

EVAL = Path(__file__).resolve().parent           # finetune/eval/
ROOT = next(p for p in EVAL.parents if (p / "backend").is_dir())  # codeAloud/
FT = ROOT / "finetune" / "data"                  # pipeline data dir
QUESTIONS = {q["id"]: q for q in json.load(open(ROOT / "backend" / "data" / "questions.json"))}
HINTS = {k: v for k, v in json.load(open(FT / "hints.json")).items() if not k.startswith("_")}

# ---------------------------------------------------------------- test split
# Recompute the held-out-by-question split exactly as build_dataset.py does.
def test_question_ids(states):
    random.seed(0)
    qids = sorted({s["question_id"] for s in states})
    random.shuffle(qids)
    n_test = max(1, round(len(qids) * 0.15))
    return set(qids[:n_test])


# ---------------------------------------------------------------- Layer A gates
_EXC = r"(Traceback|NameError|AttributeError|SyntaxError|TypeError|IndexError|KeyError|ZeroDivisionError|is not defined|has no attribute|unhashable)"


def gate_no_code(hint):
    """G1: hint must not contain solution code."""
    if "```" in hint:
        return False, "contains a code fence"
    if re.search(r"\bdef\s+\w+\s*\(", hint) or "lambda" in hint:
        return False, "contains a function definition"
    if re.search(r"\n\s{4,}\S", hint):
        return False, "contains an indented code block"
    return True, ""


def gate_no_hidden_info(hint, state):
    """G2: hint must not quote the traceback or a test's expected output."""
    if re.search(_EXC, hint):
        return False, "quotes the traceback / error text"
    for tc in QUESTIONS[state["question_id"]]["test_cases"]:
        exp = tc["output"].strip()
        # only flag structured/distinctive expected outputs (lists, quoted strs)
        if ("[" in exp or '"' in exp) and exp in hint:
            return False, f"quotes an expected output ({exp!r})"
    return True, ""


def gate_stub_minimal(hint, state):
    """G3: on a stub, the hint must be the bare 'not started' nudge."""
    if state["label"] != "stub":
        return True, ""
    if "?" in hint or "written any code" not in hint.lower():
        return False, "stub hint should be the bare 'not written' nudge, no question"
    return True, ""


def run_gates(hint, state):
    for fn in (
        lambda: gate_no_code(hint),
        lambda: gate_no_hidden_info(hint, state),
        lambda: gate_stub_minimal(hint, state),
    ):
        ok, reason = fn()
        if not ok:
            return False, reason
    return True, ""


# ---------------------------------------------------------------- Layer B prompt
RUBRIC = """You are grading a single interview HINT that an AI interviewer ("Alex") gave a candidate.
You see the problem, the candidate's current code, its execution result, and the hint.
You do NOT see any reference/ideal hint — judge the hint on its own merits.

Score three dimensions:
- appropriateness (0-3): does the hint give the right KIND of nudge for this state?
    stub -> just notes nothing is written; wrong-output -> points at the specific mistake as a question;
    suboptimal -> acknowledges it works and nudges toward improvement; runtime-error/typo -> says it crashes
    and steers to the offending line/variable; optimal -> asks the candidate for time AND space complexity.
    3=on target and specific; 2=right kind but generic/misses a nuance; 1=wrong kind or misdiagnosed; 0=unrelated.
- technical (0-2): is every claim the hint makes about the code correct? 2=all correct; 1=minor slip; 0=misdiagnosis.
- style (0-2): 2=<=3 sentences, no praise openers, leading (a question or a pointer) not a lecture; 1=one issue; 0=multiple.

Also judge the COMPLEXITY CONDUCT rule (pass/fail):
- The interviewer must NOT state/analyze the candidate's CURRENT solution complexity (e.g. "this is O(n^2)"), especially time.
- It MAY challenge toward a TARGET inside a question ("can you improve the space to O(1)?", "can you do it faster?").
- On an OPTIMAL solution, the hint MUST ask the candidate to state both time and space complexity (asking, not telling).
Set complexity_ok=false if any of these is violated, else true.

Return ONLY a JSON object: {"appropriateness":int,"technical":int,"style":int,"complexity_ok":bool,"justification":"one sentence"}."""

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "appropriateness": {"type": "integer"},
        "technical": {"type": "integer"},
        "style": {"type": "integer"},
        "complexity_ok": {"type": "boolean"},
        "justification": {"type": "string"},
    },
    "required": ["appropriateness", "technical", "style", "complexity_ok", "justification"],
    "additionalProperties": False,
}


def render_prompt(state, hint):
    q = QUESTIONS[state["question_id"]]
    tests = "\n".join(f"  {tc['input']} -> {tc['output']}" for tc in q["test_cases"])
    ex = state["execution"]
    parts = [
        RUBRIC,
        "\n--- ITEM ---",
        f"State type: {state['label']}",
        f"Problem: {q['title']} ({q['difficulty']})",
        q["description"],
        "Test cases:\n" + tests,
        "Candidate's code:\n```python\n" + state["code"].rstrip() + "\n```",
        f"Execution: status={ex['status']}, passed={ex['passed_count']}/{ex['total_count']}",
    ]
    if ex["stderr"].strip():
        parts.append("stderr: " + ex["stderr"].strip())
    parts.append("HINT TO GRADE:\n" + hint)
    return "\n".join(parts)


# ---------------------------------------------------------------- judge backends
class JudgeBackend:
    def judge(self, items):
        """items: list of {id, prompt}. Return {id: verdict} or None if the
        verdicts are not ready yet (backend handled a handoff and the caller
        should stop)."""
        raise NotImplementedError


def _extract_json(text):
    """Pull a JSON object out of a model reply that may be fenced or prefaced."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


def _write_judged(verdicts):
    EVAL.mkdir(exist_ok=True)
    with open(EVAL / "judged.jsonl", "w") as f:
        for v in verdicts.values():
            f.write(json.dumps(v, ensure_ascii=False) + "\n")


class ClaudeCLIBackend(JudgeBackend):
    """Automated, subscription-based: shells out to `claude -p` per item.

    Uses the Claude Code CLI in headless print mode — no ANTHROPIC_API_KEY, no
    per-call API bill (it draws on the Claude subscription). Runs standalone in
    any terminal.
    """

    def __init__(self, model=None):
        self.model = model  # None -> CLI's session default (Opus)

    def judge(self, items):
        import subprocess

        verdicts = {}
        for i, it in enumerate(items, 1):
            cmd = ["claude", "-p", "--output-format", "json"]
            if self.model:
                cmd += ["--model", self.model]
            cmd.append(it["prompt"])
            out = subprocess.run(cmd, capture_output=True, text=True)
            if out.returncode != 0:
                raise RuntimeError(f"claude CLI failed on {it['id']}: {out.stderr[:300]}")
            envelope = json.loads(out.stdout)
            v = _extract_json(envelope["result"])
            v["id"] = it["id"]
            verdicts[it["id"]] = v
            print(f"  judged {i}/{len(items)}  {it['id']}")
        _write_judged(verdicts)
        return verdicts


class ManualBackend(JudgeBackend):
    """Agent-in-the-loop file handoff (NOT automated). Only completes when a
    Claude Code agent driving this session reads to_judge.jsonl and writes
    judged.jsonl by hand. Use claude-cli for an automated run.
    """

    def judge(self, items):
        EVAL.mkdir(exist_ok=True)
        judged_path = EVAL / "judged.jsonl"
        if judged_path.exists():
            verdicts = {json.loads(l)["id"]: json.loads(l) for l in open(judged_path)}
            missing = [it["id"] for it in items if it["id"] not in verdicts]
            if missing:
                print(f"judged.jsonl is missing {len(missing)} ids: {missing[:5]}...")
                return None
            return verdicts
        with open(EVAL / "to_judge.jsonl", "w") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        print(
            f"\nWrote {len(items)} judge requests -> {EVAL / 'to_judge.jsonl'}\n"
            "This backend is not automated: a Claude Code agent must read each item's\n"
            "`prompt`, grade per the rubric, and write one JSON verdict per line to\n"
            "finetune/eval/judged.jsonl, then rerun. For a hands-off run use --backend claude-cli."
        )
        return None


class APIBackend(JudgeBackend):
    """Drop-in Anthropic API judge (Opus by default)."""

    def __init__(self, model):
        import anthropic  # guarded: only needed for --backend api

        self.client = anthropic.Anthropic()
        self.model = model

    def judge(self, items):
        verdicts = {}
        for it in items:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                output_config={"format": {"type": "json_schema", "schema": VERDICT_SCHEMA}},
                messages=[{"role": "user", "content": it["prompt"]}],
            )
            text = next(b.text for b in resp.content if b.type == "text")
            v = json.loads(text)
            v["id"] = it["id"]
            verdicts[it["id"]] = v
        EVAL.mkdir(exist_ok=True)
        with open(EVAL / "judged.jsonl", "w") as f:
            for v in verdicts.values():
                f.write(json.dumps(v, ensure_ascii=False) + "\n")
        return verdicts


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--predictions", help="jsonl {question_id,label,hint}; default = teacher hints")
    ap.add_argument("--backend", choices=["claude-cli", "manual", "api"], default="claude-cli")
    ap.add_argument("--model", default=None,
                    help="judge model; claude-cli defaults to the session model, api to claude-opus-4-8")
    args = ap.parse_args()

    states = [json.loads(l) for l in open(FT / "states.jsonl")]
    test_qs = test_question_ids(states)
    test_states = [s for s in states if s["question_id"] in test_qs]

    preds = {}
    if args.predictions:
        for l in open(args.predictions):
            r = json.loads(l)
            preds[f"{r['question_id']}::{r['label']}"] = r["hint"]

    # assemble items: pick hint under evaluation, run Layer A gates
    items, gate_fail = [], {}
    for s in test_states:
        key = f"{s['question_id']}::{s['label']}"
        hint = preds.get(key, HINTS.get(key))
        if hint is None:
            continue
        ok, reason = run_gates(hint, s)
        rec = {"id": key, "state": s["label"], "question": s["question_id"], "hint": hint}
        if not ok:
            gate_fail[key] = reason
        else:
            items.append({**rec, "prompt": render_prompt(s, hint)})

    if args.backend == "claude-cli":
        backend = ClaudeCLIBackend(args.model)
    elif args.backend == "manual":
        backend = ManualBackend()
    else:
        backend = APIBackend(args.model or "claude-opus-4-8")
    verdicts = backend.judge([{"id": it["id"], "prompt": it["prompt"]} for it in items])
    if verdicts is None:
        return  # claude-code phase 1: waiting for judged.jsonl

    # merge + verdict
    results = []
    for key, reason in gate_fail.items():
        results.append({"id": key, "passed": False, "reason": f"gate: {reason}"})
    for it in items:
        v = verdicts[it["id"]]
        total = v["appropriateness"] + v["technical"] + v["style"]
        passed = v["complexity_ok"] and v["appropriateness"] >= 2 and total >= 5
        results.append({
            "id": it["id"], "state": it["state"], "question": it["question"],
            "passed": passed, "total": total, "complexity_ok": v["complexity_ok"],
            **{k: v[k] for k in ("appropriateness", "technical", "style", "justification")},
        })

    _report(results)


def _report(results):
    EVAL.mkdir(exist_ok=True)
    json.dump(results, open(EVAL / "report.json", "w"), indent=2, ensure_ascii=False)
    n = len(results)
    passed = sum(r["passed"] for r in results)
    print(f"\n=== hint eval: {passed}/{n} passed ({passed / n:.0%}) ===")
    # by state type
    from collections import defaultdict
    by_state = defaultdict(lambda: [0, 0])
    for r in results:
        st = r.get("state", "?")
        by_state[st][0] += r["passed"]
        by_state[st][1] += 1
    print("by state:", {k: f"{a}/{b}" for k, (a, b) in sorted(by_state.items())})
    fails = [f"{r['id']} ({r.get('reason', 'low score')})" for r in results if not r["passed"]]
    if fails:
        print("failures:")
        for f in fails:
            print("  -", f)
    print(f"full report -> {EVAL / 'report.json'}")


if __name__ == "__main__":
    main()
