"""Stage 1 summary.

Reads results/s1/{nextword,labeled,neutral}_{tag}.jsonl for every model tag present and writes
results/s1/summary.md, plus results/s1/samples_{tag}.md with 30 random answers for a manual read of the scorer.
Rates are reported side by side; there are no thresholds here.
"""
import random
from collections import Counter, defaultdict
from statistics import mean

from common import APPROACHES, APPROACH_LABEL, RESULTS, load_prompts, read_jsonl, utf8_stdout

S1 = RESULTS / "s1"
ANSWERS = ["A", "B", "C", "other", "multiple", "none"]


def md_table(header, rows):
    out = ["| " + " | ".join(str(h) for h in header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def pct(k, n):
    return f"{100 * k / n:.0f}% ({k}/{n})" if n else "–"


def tags():
    return sorted({p.stem.split("_", 1)[1] for p in S1.glob("*_qwen*.jsonl")})


def load(tag):
    meta, data = {}, {}
    for kind in ["nextword", "labeled", "neutral"]:
        rows = read_jsonl(S1 / f"{kind}_{tag}.jsonl")
        meta[kind] = next((r for r in rows if r.get("kind") == "meta"), None)
        data[kind] = [r for r in rows if r.get("kind") in ("answer", "prompt")]
    return meta, data


def followed(rows):
    return sum(r["approach_number"] == r["approach"] for r in rows)


def dist_str(rows):
    c = Counter(r["approach_number"] for r in rows)
    return " ".join(f"{x}:{c[x]}" for x in ANSWERS if c[x]) or "–"


def section(tag, meta, data):
    L, N, W = data["labeled"], data["neutral"], data["nextword"]
    out = [f"## {tag}", ""]
    runs = []
    for k, m in meta.items():
        if not m:
            continue
        s = f"{k}: {m['time']}, {m['device']} {m['dtype'].replace('torch.', '')}"
        s += f", n={len(W)} prompts" if k == "nextword" else \
            f", T={m['temperature']}, max_new_tokens={m['max_new_tokens']}, n={len(data[k])} answers"
        runs.append(s)
    out += ["Runs: " + "; ".join(runs) if runs else "No runs found.", ""]

    # 1. headline: labeled rate next to neutral rate (+ next-word)
    rows = []
    for a in APPROACHES:
        la = [r for r in L if r["approach"] == a]
        raw = [r["approach_prob"][a] for r in W]
        tokp = [r["approach_prob_pertoken"][a] for r in W if "approach_prob_pertoken" in r]
        rows.append([APPROACH_LABEL[a], pct(sum(r["approach_number"] == a for r in la), len(la)),
                     pct(sum(r["approach_number"] == a for r in N), len(N)),
                     f"{mean(raw):.2f}" if raw else "–", f"{mean(tokp):.2f}" if tokp else "–"])
    cl = Counter(r["approach_number"] for r in L)
    cn = Counter(r["approach_number"] for r in N)
    for o in ["other", "multiple", "none"]:
        rows.append([o, pct(cl[o], len(L)), pct(cn[o], len(N)), "", ""])
    out += ["### Approach rates", "",
            "Labeled column: share of answers to prompts labeled with that approach that give its number. "
            "Neutral column: share of all neutral samples giving that number. Next-word columns: mean over prompts of "
            "the continuation-based approach probability (raw = total log-prob, favours short continuations; "
            "per token = length-normalized). other/multiple/none are shares of all labeled answers / all neutral samples.",
            "", md_table(["approach", "labeled prompts", "neutral samples", "next-word raw", "next-word per token"], rows), ""]

    if L:
        rows = []
        for a in APPROACHES:
            la = [r for r in L if r["approach"] == a]
            c = Counter(r["approach_number"] for r in la)
            rows.append([APPROACH_LABEL[a], len(la)] + [c[x] for x in ANSWERS])
        out += ["### Labeled approach × answered number", "", md_table(["labeled", "n"] + ANSWERS, rows), ""]

        by = defaultdict(list)
        for r in L:
            by[(r["approach"], r["desc_id"], r["heldout_desc"])].append(r)
        rows = [[d, a, "held out" if h else "", pct(followed(rs), len(rs)), dist_str(rs)]
                for (a, d, h), rs in sorted(by.items())]
        out += ["### Follow rate per description", "", md_table(["desc", "approach", "", "followed", "answers"], rows), ""]

        rows = []
        for key in ["frame", "position", "heldout_wording"]:
            by = defaultdict(list)
            for r in L:
                by[r[key]].append(r)
            rows += [[f"{key}={k}", pct(followed(rs), len(rs))] for k, rs in sorted(by.items())]
        out += ["### Follow rate per clause frame / position / wording split", "", md_table(["", "followed"], rows), ""]

    # per wording
    rows = []
    for w in load_prompts("neutral"):
        wid = w["wording_id"]
        ns = [r for r in N if r["wording_id"] == wid]
        ls = [r for r in L if r["wording_id"] == wid]
        nw = next((r for r in W if r["wording_id"] == wid), None)
        rows.append([wid, "H" if w["heldout_wording"] else "", dist_str(ns) if ns else "–",
                     " ".join(f"{a}:{nw['approach_prob'][a]:.2f}" for a in APPROACHES) if nw else "–",
                     " ".join(f"{a}:{nw['approach_prob_pertoken'][a]:.2f}" for a in APPROACHES)
                     if nw and "approach_prob_pertoken" in nw else "–",
                     pct(followed(ls), len(ls)) if ls else "–",
                     w["text"][:95] + ("…" if len(w["text"]) > 95 else "")])
    out += ["### Per wording (H = held-out wording)", "",
            md_table(["id", "", "neutral answers", "next-word raw", "next-word per token", "labeled followed", "wording"], rows), ""]

    if W:
        acc = defaultdict(list)
        for r in W:
            for t in r["topk"][:10]:
                acc[t["token"]].append(t["p"])
        top = sorted(acc.items(), key=lambda kv: -sum(kv[1]))[:12]
        rows = [[repr(t), f"{sum(ps) / len(W):.3f}", len(ps)] for t, ps in top]
        out += ["### Next token after the prefill", "",
                f"Prefill `{meta['nextword']['prefill']}`. Mean probability over {len(W)} prompts of the most frequent "
                "top-10 tokens (n = prompts where the token was in the top 10).", "",
                md_table(["token", "mean p", "n"], rows), ""]

    allr = L + N
    if allr:
        how = Counter(r["final_how"] for r in allr)
        both = [r for r in allr if r["agree"] is not None]
        limits = {k: meta[k]["max_new_tokens"] for k in ["labeled", "neutral"] if meta.get(k)}
        trunc = sum(r["n_tokens"] >= limits.get("labeled" if "approach" in r else "neutral", 10 ** 9) for r in allr)
        rows = [["final answer found by", " ".join(f"{k}:{v}" for k, v in how.most_common())],
                ["number label agrees with text label (both in A/B/C)", pct(sum(r["agree"] for r in both), len(both))],
                ["mentions the paradox / 'depends'", pct(sum(r["mentions_paradox"] for r in allr), len(allr))],
                ["answers that hit the token limit", pct(trunc, len(allr))],
                ["mean answer length (tokens)", f"{mean(r['n_tokens'] for r in allr):.0f}"]]
        out += ["### Scorer diagnostics", "", md_table(["", ""], rows), ""]
    return "\n".join(out)


def samples_file(tag, data):
    rng = random.Random(0)
    picks = []
    for kind in ["labeled", "neutral"]:
        rows = data[kind]
        picks += [(kind, r) for r in rng.sample(rows, min(15, len(rows)))]
    if not picks:
        return
    out = [f"# {tag}: {len(picks)} random answers for a manual read of the scorer", ""]
    for kind, r in picks:
        label = f"labeled {r['approach']} / {r['desc_id']}" if kind == "labeled" else f"neutral sample {r['sample']}"
        out += [f"## {r['id']} — {label}", "",
                f"scorer: number→**{r['approach_number']}** ({r['final_how']}, value {r['final_value']}), "
                f"text→{r['approach_text']} {r['methods_mentioned']}, paradox={r['mentions_paradox']}, {r['n_tokens']} tokens", "",
                "> " + r["prompt"].replace("\n", "\n> "), "", "```", r["answer"], "```", ""]
    (S1 / f"samples_{tag}.md").write_text("\n".join(out), encoding="utf-8")


def main():
    utf8_stdout()
    parts = ["# Stage 1 summary", "", "Generated by `s1_summarize.py` from `results/s1/*.jsonl`.", ""]
    for tag in tags():
        meta, data = load(tag)
        parts.append(section(tag, meta, data))
        samples_file(tag, data)
    text = "\n".join(parts)
    (S1 / "summary.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
