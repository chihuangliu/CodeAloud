"""Generate hint predictions on the held-out test split with any OpenAI-compatible
model, in the exact shape eval_judge.py scores.

For each held-out (question, state) this rebuilds the same system+user prompt the
model was trained on — via build_dataset.SYSTEM + render_user, byte-identical to
the rows in dataset/test.jsonl — and asks the model to produce the assistant hint.
question_id/label come from recomputing build_dataset.py's held-out-by-question
split (seed 0), so the emitted keys line up 1:1 with the judge.

    # point at a local server (vLLM / Ollama / llama.cpp / LM Studio) ...
    python -m code_aloud.fine_tune.eval.gen_predictions \
        --base-url http://localhost:8000/v1 --model my-finetuned-model

    # ... or an OpenAI-compatible cloud endpoint
    OPENAI_API_KEY=sk-... python -m code_aloud.fine_tune.eval.gen_predictions \
        --base-url https://api.openai.com/v1 --model gpt-4o-mini

Then score it:
    python -m code_aloud.fine_tune.eval.eval_judge --predictions code_aloud/fine_tune/eval/preds.jsonl

base-url / api-key also read from OPENAI_BASE_URL / OPENAI_API_KEY. Many local
servers ignore the key; a placeholder is sent so they don't 401.
"""

import argparse
import json
import os
import random
import urllib.error
import urllib.request
from pathlib import Path

from code_aloud.fine_tune.data.build_dataset import SYSTEM, render_user

EVAL = Path(__file__).resolve().parent  # code_aloud/fine_tune/eval/
FT = EVAL.parent / "data"  # pipeline data dir

HINTS = {
    k: v for k, v in json.load(open(FT / "hints.json")).items() if not k.startswith("_")
}


def test_states_in_order():
    """The ordered [(question_id, label, state), ...] of the held-out test split,
    matching dataset/test.jsonl row order exactly (build_dataset.py, seed 0)."""
    states = [json.loads(line) for line in open(FT / "states.jsonl")]
    recs = [s for s in states if HINTS.get(f"{s['question_id']}::{s['label']}")]
    random.seed(0)
    qids = sorted({s["question_id"] for s in recs})
    random.shuffle(qids)
    test_q = set(qids[: max(1, round(len(qids) * 0.15))])
    return [
        (s["question_id"], s["label"], s) for s in recs if s["question_id"] in test_q
    ]


def chat(base_url, api_key, model, messages, temperature, max_tokens, timeout):
    """One OpenAI-compatible /chat/completions call. Stdlib only."""
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    ).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"HTTP {e.code} from {base_url}: {e.read().decode()[:300]}"
        ) from None
    return payload["choices"][0]["message"]["content"].strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1"),
        help="OpenAI-compatible base URL ending in /v1 (env OPENAI_BASE_URL)",
    )
    ap.add_argument(
        "--api-key",
        default=os.environ.get("OPENAI_API_KEY", "not-needed"),
        help="API key; local servers usually ignore it (env OPENAI_API_KEY)",
    )
    ap.add_argument("--model", required=True, help="model name the endpoint serves")
    ap.add_argument(
        "--out",
        default=str(EVAL / "pred.jsonl"),
        help="output predictions jsonl (default: eval/preds.jsonl)",
    )
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--timeout", type=float, default=120)
    args = ap.parse_args()

    keys = test_states_in_order()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for i, (qid, label, state) in enumerate(keys, 1):
            # rebuild the trained prompt; the model regenerates the assistant hint
            messages = [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": render_user(state)},
            ]
            hint = chat(
                args.base_url,
                args.api_key,
                args.model,
                messages,
                args.temperature,
                args.max_tokens,
                args.timeout,
            )
            f.write(
                json.dumps(
                    {"question_id": qid, "label": label, "hint": hint},
                    ensure_ascii=False,
                )
                + "\n"
            )
            print(
                f"  {i}/{len(keys)}  {qid}::{label}  ->  {hint[:60].replace(chr(10), ' ')}..."
            )

    print(f"\nwrote {len(keys)} predictions -> {out_path}")
    print(
        f"score with:\n  python -m code_aloud.fine_tune.eval.eval_judge --predictions {out_path}"
    )


if __name__ == "__main__":
    main()
