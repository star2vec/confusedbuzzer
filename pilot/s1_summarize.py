"""Stage 1 summary.

Answers are re-scored from their text with the current score.py (the fields stored at generation time are
overwritten). Reads results/s1/{labeled,neutral}_{tag}.jsonl for every model tag present and writes results/s1/summary.md, plus
results/s1/samples_{tag}.md with 30 random answers for a manual read of the scorer. The next-word check
(nextword_*.jsonl) is not read. Primary label = method stated in the text (approach_text); secondary = final
number (approach_number). Rates are reported side by side; there are no thresholds here.

Per model: labeled accuracy (all / non-canonical wordings / canonical / held-out splits), labeled x answered
confusion, text/number agreement, neutral approach distribution per wording, and two variation readings:
across wordings (chi-square statistic on wording x {A,B,C} counts with a permutation p-value) and across samples
(majority share within a wording, next to what iid draws from the pooled mix would give).
"""
import random
from collections import Counter, defaultdict
from statistics import mean

import numpy as np

from common import APPROACHES, APPROACH_LABEL, RESULTS, load_prompts, read_jsonl, utf8_stdout
from score import score

S1 = RESULTS / "s1"
TEXT_LABELS = ["A", "B", "C", "multiple", "none"]
NUM_LABELS = ["A", "B", "C", "other", "multiple", "none"]
N_PERM = 5000


def md_table(header, rows):
    out = ["| " + " | ".join(str(h) for h in header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def pct(k, n):
    return f"{100 * k / n:.0f}% ({k}/{n})" if n else "–"


def tags():
    return sorted({p.stem.split("_", 1)[1] for p in S1.glob("*_qwen*.jsonl") if p.stem.split("_", 1)[0] in ("labeled", "neutral")})


def load(tag):
    meta, data = {}, {}
    for kind in ["labeled", "neutral"]:
        rows = read_jsonl(S1 / f"{kind}_{tag}.jsonl")
        meta[kind] = next((r for r in rows if r.get("kind") == "meta"), None)
        data[kind] = [r for r in rows if r.get("kind") == "answer"]
        for r in data[kind]:  # re-score from the text so scorer changes apply without regenerating
            r.update(score(r["answer"]))
    return meta, data


def acc(rows, key="approach_text"):
    return pct(sum(r[key] == r["approach"] for r in rows), len(rows))


def dist_str(rows, key="approach_text"):
    labels = TEXT_LABELS if key == "approach_text" else NUM_LABELS
    c = Counter(r[key] for r in rows)
    return " ".join(f"{x}:{c[x]}" for x in labels if c[x]) or "–"


def chi2_stat(table):
    table = np.asarray(table, float)
    rs, cs = table.sum(1, keepdims=True), table.sum(0, keepdims=True)
    exp = rs @ cs / table.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        term = np.where(exp > 0, (table - exp) ** 2 / exp, 0.0)
    return float(term.sum())


def across_wordings(N):
    """Chi-square statistic on wording x {A,B,C} counts (text label), p-value by permuting labels across wordings."""
    rows = [r for r in N if r["approach_text"] in APPROACHES]
    wids = sorted({r["wording_id"] for r in rows})
    if len(wids) < 2 or len({r["approach_text"] for r in rows}) < 2:
        return None
    widx = {w: i for i, w in enumerate(wids)}
    aidx = {a: i for i, a in enumerate(APPROACHES)}
    w = np.array([widx[r["wording_id"]] for r in rows])
    a = np.array([aidx[r["approach_text"]] for r in rows])

    def table(a_):
        t = np.zeros((len(wids), 3))
        np.add.at(t, (w, a_), 1)
        return t

    obs = chi2_stat(table(a))
    rng = np.random.default_rng(0)
    perm = np.array([chi2_stat(table(rng.permutation(a))) for _ in range(N_PERM)])
    df = (len(wids) - 1) * (len(set(a.tolist())) - 1)
    return dict(chi2=obs, df=df, p_perm=float((perm >= obs - 1e-9).mean()), n=len(rows), n_wordings=len(wids))


def across_samples(N):
    """Within-wording majority share among A/B/C-labeled samples, next to iid draws from the pooled mix."""
    by = defaultdict(list)
    for r in N:
        if r["approach_text"] in APPROACHES:
            by[r["wording_id"]].append(r["approach_text"])
    groups = [v for v in by.values() if len(v) >= 2]
    if not groups:
        return None
    pooled = Counter(a for v in groups for a in v)
    p = np.array([pooled[a] for a in APPROACHES], float)
    p /= p.sum()
    maj = [max(Counter(v).values()) / len(v) for v in groups]
    rng = np.random.default_rng(0)
    sim = []
    for _ in range(2000):
        sim.append(mean(np.bincount(rng.choice(3, size=len(v), p=p), minlength=3).max() / len(v) for v in groups))
    return dict(n_wordings=len(groups), mean_majority=mean(maj), single=sum(m == 1.0 for m in maj),
                expected_iid=float(np.mean(sim)), pooled={a: pooled[a] for a in APPROACHES})


def section(tag, meta, data):
    L, N = data["labeled"], data["neutral"]
    out = [f"## {tag}", ""]
    runs = []
    for k, m in meta.items():
        if m:
            runs.append(f"{k}: {m['time']}, {m['device']} {m['dtype']}, T={m['temperature']}, "
                        f"max_new_tokens={m['max_new_tokens']}, repetition_penalty={m.get('repetition_penalty')}, "
                        f"n={len(data[k])} answers")
    out += ["Runs: " + "; ".join(runs) if runs else "No runs found.", ""]

    # 1. side by side: labeled follow rate next to neutral share, text label first, number label second
    rows = []
    for a in APPROACHES:
        la = [r for r in L if r["approach"] == a]
        rows.append([APPROACH_LABEL[a],
                     pct(sum(r["approach_text"] == a for r in la), len(la)), pct(sum(r["approach_text"] == a for r in N), len(N)),
                     pct(sum(r["approach_number"] == a for r in la), len(la)), pct(sum(r["approach_number"] == a for r in N), len(N))])
    ct, cn = Counter(r["approach_text"] for r in L), Counter(r["approach_text"] for r in N)
    kt, kn = Counter(r["approach_number"] for r in L), Counter(r["approach_number"] for r in N)
    for o in ["multiple", "none", "other"]:
        rows.append([o, pct(ct[o], len(L)) if o != "other" else "", pct(cn[o], len(N)) if o != "other" else "",
                     pct(kt[o], len(L)), pct(kn[o], len(N))])
    out += ["### Approach rates (text label primary, number label secondary)", "",
            "Labeled columns: share of answers to prompts labeled with that approach whose label is that approach. "
            "Neutral columns: share of all neutral samples with that label. multiple/none/other rows are shares of all "
            "labeled answers / all neutral samples.", "",
            md_table(["approach", "labeled, text", "neutral, text", "labeled, number", "neutral, number"], rows), ""]

    if L:
        subsets = [("all wordings", L), ("non-canonical wordings (id != 0)", [r for r in L if r["wording_id"] != 0]),
                   ("canonical wording (id 0)", [r for r in L if r["wording_id"] == 0]),
                   ("held-out wordings", [r for r in L if r["heldout_wording"]]),
                   ("held-out descriptions", [r for r in L if r["heldout_desc"]]),
                   ("held-out wording and description", [r for r in L if r["heldout_wording"] and r["heldout_desc"]])]
        rows = [[name, len(rs), acc(rs, "approach_text"), acc(rs, "approach_number")] for name, rs in subsets]
        out += ["### Labeled accuracy (answer label = labeled approach)", "", md_table(["subset", "n", "text", "number"], rows), ""]

        rows = [[APPROACH_LABEL[a], len(la)] + [Counter(r["approach_text"] for r in la)[x] for x in TEXT_LABELS]
                for a in APPROACHES for la in [[r for r in L if r["approach"] == a]]]
        out += ["### Labeled approach × stated method (text label)", "", md_table(["labeled", "n"] + TEXT_LABELS, rows), ""]
        rows = [[APPROACH_LABEL[a], len(la)] + [Counter(r["approach_number"] for r in la)[x] for x in NUM_LABELS]
                for a in APPROACHES for la in [[r for r in L if r["approach"] == a]]]
        out += ["### Labeled approach × final number", "", md_table(["labeled", "n"] + NUM_LABELS, rows), ""]

    # 2. text / number agreement
    rows = []
    for name, rs in [("labeled", L), ("neutral", N), ("both", L + N)]:
        both = [r for r in rs if r["agree"] is not None]
        rows.append([name, len(rs), pct(len(both), len(rs)), pct(sum(r["agree"] for r in both), len(both))])
    out += ["### Text / number agreement", "",
            "both in A/B/C: answers where the stated method and the final number each map to one approach; agree: share of "
            "those where they match.", "", md_table(["set", "n", "both in A/B/C", "agree"], rows), ""]
    for name, rs in [("labeled", L), ("neutral", N)]:
        if rs:
            rows = [[t] + [sum(r["approach_text"] == t and r["approach_number"] == k for r in rs) for k in NUM_LABELS] for t in TEXT_LABELS]
            out += [f"#### {name}: text label (rows) × number label (columns)", "", md_table(["text \\ number"] + NUM_LABELS, rows), ""]

    if L:
        by = defaultdict(list)
        for r in L:
            by[(r["approach"], r["desc_id"], r["heldout_desc"])].append(r)
        rows = [[d, a, "held out" if h else "", acc(rs), dist_str(rs)] for (a, d, h), rs in sorted(by.items())]
        out += ["### Follow rate per description (text label)", "", md_table(["desc", "approach", "", "followed", "stated methods"], rows), ""]
        rows = []
        for key in ["frame", "position", "heldout_wording"]:
            by = defaultdict(list)
            for r in L:
                by[r[key]].append(r)
            rows += [[f"{key}={k}", acc(rs), acc(rs, "approach_number")] for k, rs in sorted(by.items())]
        out += ["### Follow rate per clause frame / position / wording split", "", md_table(["", "text", "number"], rows), ""]

    # 3. neutral distribution per wording
    rows = []
    for w in load_prompts("neutral"):
        wid = w["wording_id"]
        ns = [r for r in N if r["wording_id"] == wid]
        ls = [r for r in L if r["wording_id"] == wid]
        abc = [r["approach_text"] for r in ns if r["approach_text"] in APPROACHES]
        maj = f"{max(Counter(abc).values()) / len(abc):.1f} ({len(abc)})" if abc else "–"
        rows.append([wid, "H" if w["heldout_wording"] else "", dist_str(ns) if ns else "–", maj,
                     dist_str(ns, "approach_number") if ns else "–", acc(ls) if ls else "–",
                     w["text"][:90] + ("…" if len(w["text"]) > 90 else "")])
    out += ["### Neutral samples per wording (H = held-out wording)", "",
            "majority: share of the most frequent approach among the wording's A/B/C-labeled samples (count of such samples).", "",
            md_table(["id", "", "stated method", "majority", "final number", "labeled followed", "wording"], rows), ""]

    if N:
        aw, asmp = across_wordings(N), across_samples(N)
        rows = []
        if asmp:
            rows.append(["pooled stated method over A/B/C-labeled samples", " ".join(f"{a}:{n}" for a, n in asmp["pooled"].items())])
        if aw:
            rows.append([f"across wordings: chi-square on {aw['n_wordings']} wordings × 3 approaches ({aw['n']} samples)",
                         f"χ² = {aw['chi2']:.1f}, df = {aw['df']}, permutation p = {aw['p_perm']:.3f}"])
        else:
            rows.append(["across wordings", "not computed (fewer than 2 wordings or 1 approach)"])
        if asmp:
            rows.append([f"across samples: mean within-wording majority share ({asmp['n_wordings']} wordings)",
                         f"{asmp['mean_majority']:.2f}; expected {asmp['expected_iid']:.2f} if every sample were an iid draw from the pooled mix"])
            rows.append(["wordings whose A/B/C-labeled samples all state the same method", f"{asmp['single']}/{asmp['n_wordings']}"])
        out += ["### Variation of the neutral stated method", "", md_table(["", ""], rows), ""]

    allr = L + N
    if allr:
        how = Counter(r["final_how"] for r in allr)
        limits = {k: meta[k]["max_new_tokens"] for k in ["labeled", "neutral"] if meta.get(k)}
        trunc = sum(r["n_tokens"] >= limits.get("labeled" if "approach" in r else "neutral", 10 ** 9) for r in allr)
        rows = [["final answer found by", " ".join(f"{k}:{v}" for k, v in how.most_common())],
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
                f"scorer: text→**{r['approach_text']}** (hits {r.get('method_hits')}), "
                f"number→**{r['approach_number']}** ({r['final_how']}, value {r['final_value']}), "
                f"paradox={r['mentions_paradox']}, {r['n_tokens']} tokens", "",
                "> " + r["prompt"].replace("\n", "\n> "), "", "```", r["answer"], "```", ""]
    (S1 / f"samples_{tag}.md").write_text("\n".join(out), encoding="utf-8")


def main():
    utf8_stdout()
    parts = ["# Stage 1 summary", "", "Generated by `s1_summarize.py` from `results/s1/{labeled,neutral}_*.jsonl`. "
             "Text label (stated method) is primary, final number secondary.", ""]
    for tag in tags():
        meta, data = load(tag)
        parts.append(section(tag, meta, data))
        samples_file(tag, data)
    text = "\n".join(parts)
    (S1 / "summary.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
