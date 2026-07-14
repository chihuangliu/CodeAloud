# Fine-tune hint eval pipeline.
#
#   make gen-pred            MODEL=gpt-4o-mini BASE_URL=https://api.openai.com/v1 API_KEY=sk-...
#   make judge               MODEL=gpt-4o-mini
#   make gen-pred-and-judge  MODEL=gpt-4o-mini BASE_URL=... API_KEY=...
#
# pred.jsonl / judged.jsonl / report.json all land in OUTPUT_DIR (default:
# eval/eval_res/<MODEL>). Override any variable on the command line.

PY       := uv run python
EVAL_PKG := code_aloud.fine_tune.eval

# --- shared ---------------------------------------------------------------
MODEL      ?=
OUTPUT_DIR ?= code_aloud/fine_tune/eval/eval_res/$(MODEL)

# --- gen-pred (gen_test_pred.py) ------------------------------------------
BASE_URL    ?= http://localhost:11434/v1
API_KEY     ?= not-needed
TEMPERATURE ?= 0.0
MAX_TOKENS  ?= 1024

# --- judge (eval_judge.py) ------------------------------------------------
BACKEND     ?= claude-cli
JUDGE_MODEL ?=

.PHONY: gen-pred judge gen-pred-and-judge

## gen-pred: generate hint predictions on the test split -> OUTPUT_DIR/pred.jsonl
gen-pred:
	@test -n "$(MODEL)" || { echo "MODEL is required, e.g. make gen-pred MODEL=gpt-4o-mini"; exit 1; }
	$(PY) -m $(EVAL_PKG).gen_test_pred \
		--model "$(MODEL)" \
		--base-url "$(BASE_URL)" \
		--api-key "$(API_KEY)" \
		--out "$(OUTPUT_DIR)/pred.jsonl" \
		--temperature $(TEMPERATURE) \
		--max-tokens $(MAX_TOKENS)

## judge: score OUTPUT_DIR/pred.jsonl -> OUTPUT_DIR/judged.jsonl + report.json
judge:
	$(PY) -m $(EVAL_PKG).eval_judge \
		--output-dir "$(OUTPUT_DIR)" \
		--backend "$(BACKEND)" \
		$(if $(JUDGE_MODEL),--model "$(JUDGE_MODEL)")

## gen-pred-and-judge: generate predictions then score them
gen-pred-and-judge: gen-pred judge
