# Pilot log

Light running log, newest entry last. Numbers go here after each stage; decisions are the researcher's.

## 2026-10-08 — setup

- Models: Qwen2.5-1.5B-Instruct and Qwen2.5-3B-Instruct, both already in the Mac's HF cache. They match the brief's sizes.
- Mac runs forward-only work (next-word check, activations, probe) in fp32. The Windows RTX 2000 Ada runs generation in bf16, batch ≤ 4 for the 3B.
- Env: uv + Python 3.11, `pyproject.toml` in pilot/. Windows resolves CUDA torch from the cu124 index through a platform marker, so `uv sync` works on both machines.
- No gates or thresholds. After each stage the numbers go in this log with a sentence or two, then work stops until the researcher decides.

## 2026-10-08 — stage 1 prepared; next-word check run for the 1.5B

- Prompts (`prompts/build_prompts.py`, seed 7): 18 neutral wordings from object × threshold × radius × order × verb, each value 3–7 times, canonical Bertrand text included. 5 wordings held out (ids 1, 2, 4, 5, 17); they share no (object, threshold, radius) triple with a training wording and cover all three objects and thresholds. 8 descriptions per approach, 3 held out and written without the training ones' keywords; 3 clause frames × 2 positions (clause before or after the problem). Labeled = 18 × 3 × 8 = 432. For the probe later: train 195, strict held-out 45 (one example = 2.2 points), description-only 117, wording-only 75.
- Scorer (`score.py`): the final number gives the approach; a boxed answer always wins; bare 0 and 1 count as numbers (a 1.5B greedy answer ended in `\boxed{0}`, and the first scorer version mislabeled it as B from a 1/2 in a formula). 25 self-test cases pass. Keyword label from the solution text is kept as a secondary column.
- Generation settings: greedy for labeled prompts; neutral sampling at T = 0.7, top_p 0.95, Qwen's top_k off; Qwen's shipped repetition_penalty 1.1 kept in both; max_new_tokens 768 because one full greedy 1.5B answer ran 535 tokens.
- Next-word check, 1.5B (fp32 on MPS, 18 prompts, `results/s1/nextword_qwen1.5b.jsonl`, table in `results/s1/summary.md`). After "Solution: we choose the chord/segment by", the top next tokens are ' choosing' (mean p 0.14), ' randomly' (0.10), ' drawing' (0.10), ' the' and ' its' (0.06). No single token decides an approach, hence the continuation scoring. The raw continuation score gives P(A) ≈ 1.00 on every prompt, but A's continuations are the shortest (7–9 tokens vs up to 13), so that is mostly length. Length-normalized: A 0.42–0.52, B 0.23–0.29, C 0.24–0.30, nearly the same on all 18 wordings (canonical wording 0.47 / 0.25 / 0.27). Looks like a mild, uniform lean to endpoints before anything is written; the sampling run will show whether the written approach matches.
- 3B next-word check did not run in fp32 on the Mac: 12.4 GB of weights against an 11.5 GB recommended MPS working set; the process went to swap (24.6 GB in use) and made no progress in 8 min, so it was killed. Options: (a) 3B forward-only in bf16 on the Mac (the checkpoint's native dtype, deviates from the fp32 rule), (b) CPU fp32 on a machine with more than 16 GB RAM, (c) judge the 3B from its generation runs alone.
- Hand-off to Windows: `s1_generate.py --set labeled` and `--set neutral` for both models (commands in README; resumable), push `results/s1/*.jsonl`, then `s1_summarize.py`. Stage-2 and stage-3 scripts are written and compile; they get smoke-tested once stage 1 is in. Waiting for the researcher.
