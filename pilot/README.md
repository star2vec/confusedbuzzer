# pilot

Bertrand pilot: can a small model's choice of approach (endpoints 1/3, radial 1/2, midpoint 1/4) be read from its
activations before it writes, and can that direction steer what it writes? Running log in `LOG.md`.

## Setup (both machines)

Needs [uv](https://docs.astral.sh/uv/). From this folder:

    uv sync

Windows resolves CUDA torch from the cu124 index automatically (needs an NVIDIA driver >= 550). Check with
`uv run python -c "import torch; print(torch.cuda.is_available())"`. Models download from the HF hub on first use.

Any script takes `--limit N` for a smoke test (`--max_new_tokens 60` shortens generation). Generation scripts are
resumable: re-run the same command after an interruption. `--device cpu|mps|cuda` overrides auto-detection.

## Stage 1: behavior

Mac (forward-only, fp32):

    uv run python s1_nextword.py --model 1.5b
    uv run python s1_nextword.py --model 3b

Windows (generation, bf16; 3B uses batch 4):

    uv run python s1_generate.py --model 1.5b --set labeled
    uv run python s1_generate.py --model 1.5b --set neutral
    uv run python s1_generate.py --model 3b --set labeled
    uv run python s1_generate.py --model 3b --set neutral

Then `git add results/s1 && git commit && git push`. Summary on any machine: `uv run python s1_summarize.py`
(writes `results/s1/summary.md` and `results/s1/samples_{tag}.md`).

## Stage 2: probe (Mac, model chosen by the researcher)

    uv run python s2_activations.py --model 1.5b
    uv run python s2_probe.py --model 1.5b

Writes `results/s2/summary_{tag}.md`, `probe_{tag}.json` and `direction_{tag}.npz` (the activations `.npz` is
gitignored; the direction file is small and committed for stage 3).

## Stage 3: steering sweep (Windows)

    uv run python s3_steer.py --model 1.5b --wordings 0 3 7 9 11 14
    uv run python s3_summarize.py

Pick the six `--wordings` from the stage-1 behaviour. `--alphas 0 1 2 4 8` and `--direction classifier|diffmeans`
are the knobs.

## Files

- `prompts/build_prompts.py` regenerates `prompts/*.jsonl` deterministically (18 neutral, 432 labeled).
- `score.py` labels an answer by its final number (run it to self-test).
- `common.py` holds model loading, the chat template, residual-stream recording and the steering hook.
