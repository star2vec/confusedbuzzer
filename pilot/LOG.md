# Pilot log

Light running log, newest entry last. Numbers go here after each stage; decisions are the researcher's.

## 2026-10-08 — setup

- Models: Qwen2.5-1.5B-Instruct and Qwen2.5-3B-Instruct, both already in the Mac's HF cache. They match the brief's sizes.
- Mac runs forward-only work (next-word check, activations, probe) in fp32. The Windows RTX 2000 Ada runs generation in bf16, batch ≤ 4 for the 3B.
- Env: uv + Python 3.11, `pyproject.toml` in pilot/. Windows resolves CUDA torch from the cu124 index through a platform marker, so `uv sync` works on both machines.
- No gates or thresholds. After each stage the numbers go in this log with a sentence or two, then work stops until the researcher decides.

## 2026-10-08 — stage 1 prepared; next-word check run for the 1.5B

(Several points in this entry were changed the same day on the researcher's instructions; see the next entry.)

- Prompts (`prompts/build_prompts.py`, seed 7): 18 neutral wordings from object × threshold × radius × order × verb, each value 3–7 times, canonical Bertrand text included. 5 wordings held out (ids 1, 2, 4, 5, 17); they share no (object, threshold, radius) triple with a training wording and cover all three objects and thresholds. 8 descriptions per approach, 3 held out and written without the training ones' keywords; 3 clause frames × 2 positions (clause before or after the problem). Labeled = 18 × 3 × 8 = 432. For the probe later: train 195, strict held-out 45 (one example = 2.2 points), description-only 117, wording-only 75.
- Scorer (`score.py`): the final number gives the approach; a boxed answer always wins; bare 0 and 1 count as numbers (a 1.5B greedy answer ended in `\boxed{0}`, and the first scorer version mislabeled it as B from a 1/2 in a formula). 25 self-test cases pass. Keyword label from the solution text is kept as a secondary column.
- Generation settings: greedy for labeled prompts; neutral sampling at T = 0.7, top_p 0.95, Qwen's top_k off; Qwen's shipped repetition_penalty 1.1 kept in both; max_new_tokens 768 because one full greedy 1.5B answer ran 535 tokens.
- Next-word check: the 1.5B numbers and the 3B fp32 failure that were logged here were removed when the check was dropped from reporting (next entry); `s1_nextword.py` stays in the repo.
- Hand-off to Windows: `s1_generate.py --set labeled` and `--set neutral` for both models (commands in README; resumable), push `results/s1/*.jsonl`, then `s1_summarize.py`. Stage-2 and stage-3 scripts are written and compile; they get smoke-tested once stage 1 is in. Waiting for the researcher.

## 2026-10-08 — changes before the Windows runs (researcher's), one line on why each

- Prompts: every wording says "chord"; the two "segment with endpoints" objects are gone. Why: those phrasings change what the model is asked about, not how the chord problem is worded, and the variation should stay inside the chord problem. Regenerated with the same seed and constraints minus the object axis: 18 wordings, held out ids 2, 4, 10, 14, 15. The strict held-out rule still held (no (threshold, radius) pair shared with a training wording; held-out covers all three threshold phrasings), so nothing was relaxed. Labeled still 432; splits 195 / 45 / 117 / 75 unchanged.
- Scorer: the method stated in the text is the primary label, the final number the secondary one; their agreement is reported. Why: the number can be the textbook value for a method the text never used, or a slip for the method it did use, and the stated method is what stage 2 will label neutral samples by. "none" and "multiple" kept. Keyword markers per approach are matched sentence by sentence (lists in `score.py`); a "distance uniform" sentence that also mentions the midpoint or the disk's area is not counted for B, since that is C's derivation. The two cross-vocabulary descriptions (b4, c3) will often read as "multiple" when the model restates them. 36 self-test cases pass.
- Generation: repetition_penalty 1.0 everywhere (Qwen ships 1.1). Why: the penalty bends the token distribution the samples are meant to reflect, including on repeated numbers and method words.
- Precision: half precision on every machine, bf16 on CUDA, fp16 on MPS; the fp32 rule is dropped. Why: fp32 did not fit the 3B on the Mac, and one precision on both machines keeps Mac forward passes comparable with Windows generations.
- Next-word check dropped from the summary and this log; `s1_nextword.py` stays. Why: the prefilled continuation scores are length-sensitive and the top next tokens fix no approach; stage 1 is read from full answers. The earlier numbers were removed from the entry above and the stale `results/s1/nextword_qwen1.5b.jsonl` (old prompts) deleted.
- Third model: Qwen2.5-7B-Instruct in 4-bit (bitsandbytes nf4, bf16 compute, `--model 7b`), same stage-1 runs, default batch 2 (raise `--batch_size` if memory allows). Why: a more capable model that still fits the 8 GB GPU, to see whether the behaviour changes with scale. bitsandbytes is a Windows-only dependency (no MPS build); the 4-bit path could not be exercised on the Mac.
- Stage-1 report, per model: labeled accuracy on non-canonical wordings (and on the other splits), text/number agreement, the neutral stated-method distribution per wording, and whether it varies across wordings (chi-square on wording × approach counts, permutation p-value) and across samples (within-wording majority share next to what iid draws from the pooled mix would give). Why: these are the questions stage 2 depends on: does the model follow a stated approach on rewordings, do the two readings of an answer agree, and is the neutral choice a property of the wording or of the sample.
- Stage 2 will change: the probe trains on neutral samples labeled by their own stated method, at the last prompt token and at each of the first ~30 generated tokens. The current s2 scripts were left as they are and not smoke-tested.
- Smoke test on the Mac (1.5B, fp16 on MPS, repetition_penalty 1.0): 8 labeled greedy answers on mixed prompts and 3 neutral wordings × 3 samples, 5.6–6.5 min per batch of 8 at 768 max tokens; the files were deleted afterwards so the Windows runs regenerate them. Labeled: stated method = labeled method in 3/8 (a0, b1, b7); B stated for a6 (an A prompt) and for c0 and c3 (C prompts); no method stated for b4 and c5. Final number = labeled value in 1/8; 4/8 ended in 1/2. Text and number agreed in all 3 answers where both were readable. Neutral: 3/9 samples stated a method (A, A, C), 6/9 none; 6/9 ended in a non-canonical number (2√3/3, 1/8, 1/6, 1, …); 2/17 answers hit the token limit. The 1.5B mostly reasons from the chord-length formula 2√(r²−d²) without saying how d is drawn, hence the many "none". The markers were tuned on these answers: a generic "defined by two points on the circle" and "the length of the diameter" no longer count as methods, and "the central angle is uniformly distributed" counts as A. `s1_summarize.py` re-scores answers from their text, so later scorer fixes need no regeneration.
- Hand-off: Windows runs the six `s1_generate.py` commands in the README (labeled and neutral for 1.5b, 3b, 7b; resumable), pushes `results/s1/*.jsonl`; then `s1_summarize.py` and the stage-1 numbers go here. Waiting for the researcher.

## 2026-10-09 — stage 1 run on Windows (1.5B, 3B); 7B not run

- Runs: RTX 2000 Ada, bf16, default batch sizes (8 for the 1.5B, 4 for the 3B, 6.4 GB in use), no out-of-memory errors. Per model, 432 labeled greedy answers and 18 wordings × 10 neutral samples at T = 0.7. Wall time: 1.5B about 21 + 10 min, 3B about 52 + 26 min. The machine's stored HF token is rejected, so the runs used `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` (the Qwen models are public).
- Scoring change (researcher's): the final number (1/3 A, 1/2 B, 1/4 C) is now the primary label and the stated method is a check next to it. The keyword markers were not retuned. The per-wording table has a new column for samples that end in a canonical number but state no method, split by number. `s1_summarize.py` also writes `read_neutral_qwen3b.md` (all 180 3B neutral answers) and `read_labeled_qwen3b.md` (60 labeled 3B answers, 20 per approach, 2–3 per description) for reading by hand.
- How the two variation readings work. Across wordings: count A/B/C per wording, measure how unevenly the mix is spread over the wordings, and compare that spread with what you get after shuffling the labels among wordings (5000 shuffles). A large share of shuffles that spread at least as much means the wordings differ no more than chance. Within a wording: the average share of samples that land on the wording's most common approach, next to the share that independent draws from the pooled mix would give.

Final number (primary), with the stated method as a check:

| | 1.5B | 3B |
|---|---|---|
| labeled, number = labeled approach (all 432) | 25% | 46% |
| ... non-canonical wordings / held-out wording and description | 26% / 20% | 46% / 42% |
| ... per approach A / B / C | 16% / 46% / 14% | 26% / 57% / 56% |
| labeled, stated method = labeled approach (check) | 33% | 43% |
| labeled, number ends in something other than 1/3, 1/2 or 1/4 | 54% | 25% |
| number and stated method agree, where both are A/B/C (labeled) | 83% of 109 | 92% of 194 |
| neutral, number A / B / C / other (of 180) | 28 / 39 / 6 / 100 | 40 / 49 / 28 / 62 |
| neutral samples with a canonical number but no stated method | 57 of 73 | 61 of 117 |
| neutral, stated method A / B / C / none (check) | 11 / 13 / 7 / 146 | 20 / 13 / 42 / 100 |
| across wordings: shuffles spreading as much or more (number; stated) | 41%; 52% | 82%; 28% |
| within a wording: mean majority share vs independent draws (number) | 0.68 vs 0.66 | 0.53 vs 0.55 |
| answers that hit the 768-token limit (all) | 9% | 7% |

The 3B follows a stated approach about twice as often as the 1.5B, mostly for B and C (A is followed in about a quarter of answers and often ends in 1/2 or 1/4). The 1.5B ends in a non-canonical number in about half its answers. In neither model does the neutral choice look like a property of the wording: the mix across wordings is no more uneven than shuffled labels, and samples of one wording agree no more often than independent draws from the pooled mix would. Most neutral answers that end in 1/3, 1/2 or 1/4 do not state a method. Full tables are in `results/s1/summary.md`. Waiting for the researcher.
