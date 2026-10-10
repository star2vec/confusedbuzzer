"""Figures for the write-up. Regenerates every figure from the results files.

  uv run python figures.py

Writes results/figures/{header,phrasings,which,how,famous_number,where_we_look,when}.{png,svg} (PNG 1600 px wide),
results/figures/numbers.md (every number each figure draws) and results/figures/captions.md.
Inputs: prompts/{neutral,labeled}.jsonl, results/s1/neutral_qwen{3b,7b}.jsonl (re-scored with score.py),
results/s1/judge_qwen{3b,7b}.jsonl, results/s2/word_probe_qwen7b.json, results/s2/acts_word_qwen7b_meta.jsonl and the
7B tokenizer (token strip only).
"""
import json
import random
import textwrap
from collections import Counter, defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Arc, Circle, FancyBboxPatch, Polygon, Rectangle, Wedge  # noqa: E402

from common import PROMPTS, RESULTS, chat_prompt, read_jsonl  # noqa: E402
from score import score  # noqa: E402

OUT = RESULTS / "figures"
WIDTH_IN, DPI = 10.0, 160  # 1600 px wide
NUMS = ["1/3", "1/2", "1/4"]
COL = {"1/3": "#3b6fb6", "1/2": "#e08a2b", "1/4": "#3a9a5b", "other": "#9a9a9a"}
APP2NUM = {"A": "1/3", "B": "1/2", "C": "1/4"}
VAR2NUM = {"angle at the center": "1/3", "distance from the center": "1/2", "midpoint in the disk": "1/4"}
VAR_SHORT = {"angle at the center": "angle", "distance from the center": "distance", "midpoint in the disk": "midpoint"}
ACCENT = "#8a6bbd"  # header shading: deliberately not one of the number colors
INK = "#222222"
THR_ORDER = ["triangle", "rsqrt3", "numeric"]
THR_LABEL = {"triangle": "triangle", "rsqrt3": "r√3", "numeric": "numeric"}
RAD_ORDER = ["unspecified", "1", "2", "5"]
RAD_LABEL = {"unspecified": "r", "1": "r=1", "2": "r=2", "5": "r=5"}
STRIP_EXAMPLE = (2, 7)  # 7B derived 1/2; first variable word at answer token 68 (chosen for fit; median is 110)
RECALLED_EXAMPLE = (12, 26)  # 7B recalled 1/3: computes 2/3, boxes 1/3
RECALLED_LINES = [0, None, 10, None, 18, None, 22, None, 26, 28, 29, None, 31]  # None = "…"
RECALLED_MARK = {26: "other", 29: "boxed"}

plt.rcParams.update({
    "font.size": 15, "axes.labelsize": 16, "xtick.labelsize": 14, "ytick.labelsize": 14, "legend.fontsize": 14,
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "hatch.linewidth": 1.6, "svg.fonttype": "none", "text.usetex": False,
})
NUMBERS, CAPTIONS = [], {}


def note(fig, lines):
    NUMBERS.append(f"## {fig}\n")
    NUMBERS.extend(lines)
    NUMBERS.append("")


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    w = fig.get_size_inches()[0]
    fig.savefig(OUT / f"{name}.png", dpi=1600 / w)
    fig.savefig(OUT / f"{name}.svg")
    plt.close(fig)


def esc(s):
    return s.replace("$", r"\$")


def recalled_patch_kw(num):
    return dict(facecolor=matplotlib.colors.to_rgba(COL[num], 0.18), edgecolor=COL[num], hatch="//", linewidth=1.2)


# ---------------------------------------------------------------- data
def neutral_prompts():
    return {r["wording_id"]: r for r in read_jsonl(PROMPTS / "neutral.jsonl")}


def numbers_per_phrasing(tag):
    out = defaultdict(Counter)
    for r in read_jsonl(RESULTS / "s1" / f"neutral_{tag}.jsonl"):
        if r.get("kind") != "answer":
            continue
        a = score(r["answer"])["approach_number"]
        out[r["wording_id"]][APP2NUM.get(a, "other")] += 1
    return out


def judge(tag):
    return read_jsonl(RESULTS / "s1" / f"judge_{tag}.jsonl")


# ---------------------------------------------------------------- 1 header
def robot(ax, x0, y0, s):
    """Puzzled line robot centered at (x0, y0), size s. Tilted head, uneven eyes and brows, wavy mouth, bent antenna."""
    tilt = np.deg2rad(-10)
    R = np.array([[np.cos(tilt), -np.sin(tilt)], [np.sin(tilt), np.cos(tilt)]])
    T = lambda pts: (np.asarray(pts) * s) @ R.T + [x0, y0]
    lw = 2.6
    head = FancyBboxPatch((-0.5, -0.4), 1.0, 0.8, boxstyle="round,pad=0,rounding_size=0.22", fill=False, lw=lw, ec=INK)
    head.set_transform(matplotlib.transforms.Affine2D().scale(s).rotate(tilt).translate(x0, y0) + ax.transData)
    ax.add_patch(head)
    for (ex, ey), r in [((-0.2, 0.08), 0.065), ((0.21, 0.06), 0.045)]:
        c = T([ex, ey])
        ax.add_patch(Circle(c, r * s, color=INK))
    ax.plot(*T([[-0.32, 0.22], [-0.08, 0.30]]).T, color=INK, lw=lw, solid_capstyle="round")  # raised, slanted brow
    ax.plot(*T([[0.1, 0.2], [0.32, 0.2]]).T, color=INK, lw=lw, solid_capstyle="round")  # flat brow
    xm = np.linspace(-0.2, 0.2, 40)
    ax.plot(*T(np.c_[xm, -0.2 + 0.035 * np.sin(xm * 40)]).T, color=INK, lw=lw, solid_capstyle="round")  # wavy mouth
    ax.plot(*T([[0.0, 0.4], [0.03, 0.55], [0.14, 0.64]]).T, color=INK, lw=lw, solid_capstyle="round")  # bent antenna
    ax.add_patch(Circle(T([0.14, 0.64]), 0.05 * s, fill=False, lw=lw, ec=INK))
    ax.text(x0 + 0.85 * s, y0 + 0.15 * s, "?", fontsize=44, color=INK, ha="center", va="center", fontweight="bold")


def fig_header():
    rng = np.random.default_rng(3)
    fig = plt.figure(figsize=(WIDTH_IN, WIDTH_IN / 3))
    axes = [fig.add_axes([0.04 + i * 0.33, 0.30, 0.25, 0.68]) for i in range(3)]
    tri = [np.deg2rad(90 + 120 * i) for i in range(3)]
    lines = []
    for i, ax in enumerate(axes):
        ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15)
        ax.add_patch(Circle((0, 0), 1, fill=False, lw=2.2, ec=INK))
        ax.add_patch(Polygon([[np.cos(a), np.sin(a)] for a in tri], closed=True, fill=False, lw=1.6, ec="#b5b5b5"))
    # (a) endpoint at the top triangle vertex; favourable arc = the third opposite it
    ax = axes[0]
    p = tri[0]
    ax.add_patch(Arc((0, 0), 2, 2, theta1=np.rad2deg(p) + 120, theta2=np.rad2deg(p) + 240, lw=9, color=ACCENT, alpha=0.55))
    q = p + np.deg2rad(rng.uniform(140, 220))
    ax.plot([np.cos(p), np.cos(q)], [np.sin(p), np.sin(q)], color=INK, lw=2.4)
    for a in (p, q):
        ax.add_patch(Circle((np.cos(a), np.sin(a)), 0.05, color=INK, zorder=5))
    lines.append(f"(a) endpoints at {np.rad2deg(p) % 360:.0f}° and {np.rad2deg(q) % 360:.0f}°; shaded arc 210°–330° (one third)")
    # (b) random radius, inner half shaded, random point, perpendicular chord
    ax = axes[1]
    th = rng.uniform(0, 2 * np.pi)
    u = np.array([np.cos(th), np.sin(th)])
    ax.plot([0, u[0]], [0, u[1]], color="#777777", lw=1.6)
    ax.plot([0, 0.5 * u[0]], [0, 0.5 * u[1]], color=ACCENT, lw=9, alpha=0.55, solid_capstyle="butt")
    dd = rng.uniform(0.15, 0.45)
    h = np.sqrt(1 - dd ** 2)
    v = np.array([-u[1], u[0]])
    c1, c2 = dd * u + h * v, dd * u - h * v
    ax.plot([c1[0], c2[0]], [c1[1], c2[1]], color=INK, lw=2.4)
    ax.add_patch(Circle(dd * u, 0.05, color=INK, zorder=5))
    ax.add_patch(Circle((0, 0), 0.035, color="#777777"))
    lines.append(f"(b) radius at {np.rad2deg(th) % 360:.0f}°, point at {dd:.2f} r; shaded inner half of the radius")
    # (c) inner circle r/2 shaded, random midpoint inside, its chord
    ax = axes[2]
    ax.add_patch(Circle((0, 0), 0.5, color=ACCENT, alpha=0.30, lw=0))
    ax.add_patch(Circle((0, 0), 0.5, fill=False, color=ACCENT, lw=1.6))
    rr, ph = 0.5 * np.sqrt(rng.uniform(0.1, 0.8)), rng.uniform(0, 2 * np.pi)
    m = rr * np.array([np.cos(ph), np.sin(ph)])
    u = m / np.linalg.norm(m); v = np.array([-u[1], u[0]]); h = np.sqrt(1 - rr ** 2)
    ax.plot([(m + h * v)[0], (m - h * v)[0]], [(m + h * v)[1], (m - h * v)[1]], color=INK, lw=2.4)
    ax.add_patch(Circle(m, 0.05, color=INK, zorder=5))
    lines.append(f"(c) midpoint at {rr:.2f} r, angle {np.rad2deg(ph) % 360:.0f}°; shaded inner disk radius r/2")
    for ax, lab in zip(axes, "abc"):
        ax.text(-1.12, 1.08, f"({lab})", fontsize=17, va="top")
    rax = fig.add_axes([0.40, 0.0, 0.20, 0.30]); rax.set_aspect("equal"); rax.axis("off")
    rax.set_xlim(-1.4, 1.6); rax.set_ylim(-0.75, 0.95)
    robot(rax, 0.0, 0.0, 1.0)
    save(fig, "header")
    note("header", lines + ["No numbers drawn; favourable regions in one accent color (not a number color)."])
    CAPTIONS["header"] = ("Three ways to draw a chord at random in the same circle, with the inscribed equilateral triangle: "
                          "(a) two random points on the circle, (b) a random point on a random radius, with the chord at right "
                          "angles to it, (c) a random midpoint in the disk. The shaded part marks where the chord comes out "
                          "longer than the triangle's side.")


# ---------------------------------------------------------------- 2 phrasings
def fig_phrasings():
    P = neutral_prompts()
    rng = random.Random(0)
    picks = rng.sample(range(1, 18), 2)
    lab = [r for r in read_jsonl(PROMPTS / "labeled.jsonl")]
    L = rng.choice(lab)
    clause = L["text"].replace(P[L["wording_id"]]["text"], "").strip()
    boxes = [("canonical problem statement (id 0)", P[0]["text"], None),
             (f"rephrasing, id {picks[0]}", P[picks[0]]["text"], None),
             (f"rephrasing, id {picks[1]}", P[picks[1]]["text"], None),
             (f"labeled prompt {L['id']} (approach {L['approach']}, {APP2NUM[L['approach']]})", L["text"], clause)]
    fig = plt.figure(figsize=(WIDTH_IN, 9.0 * 0.80))
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0.20, 1)
    y = 0.97
    width_chars = 78
    for head, text, hl in boxes:
        ax.text(0.04, y, head, fontsize=14, color="#555555", va="top", style="italic")
        y -= 0.04
        if hl is None:
            wrapped = textwrap.wrap(text, width_chars)
            spans = [(w, False) for w in wrapped]
        else:
            before, after = text.split(hl) if hl in text else (text, "")
            spans = []
            pre = textwrap.wrap(before.strip(), width_chars)
            spans += [(w, False) for w in pre]
            spans += [(w, True) for w in textwrap.wrap(hl, width_chars)]
            spans += [(w, False) for w in textwrap.wrap(after.strip(), width_chars)]
        top = y + 0.012
        for w, is_hl in spans:
            kw = dict(bbox=dict(boxstyle="square,pad=0.15", fc=matplotlib.colors.to_rgba(COL[APP2NUM[L["approach"]]], 0.25), ec="none")) if is_hl else {}
            ax.text(0.06, y, esc(w), fontsize=15, va="top", family="DejaVu Sans", **kw)
            y -= 0.038
        ax.add_patch(Rectangle((0.035, y + 0.012), 0.93, top - y - 0.006, fill=False, ec="#bbbbbb", lw=1.2))
        y -= 0.045
    save(fig, "phrasings")
    note("phrasings", [f"canonical id 0; rephrasings ids {picks[0]}, {picks[1]} (random.Random(0)); labeled prompt {L['id']} "
                       f"(approach {L['approach']}, description {L['desc_id']}, clause {L['position']} the problem)",
                       f"highlighted clause: \"{clause}\""])
    CAPTIONS["phrasings"] = ("Prompts as the model sees them. Top: the canonical Bertrand problem statement and two of the 17 "
                             "rephrasings (ids picked at random). Bottom: a labeled prompt, with the clause that states the "
                             "approach highlighted.")


# ---------------------------------------------------------------- 3 which
def fig_which():
    P = neutral_prompts()
    order = sorted(P, key=lambda w: (THR_ORDER.index(P[w]["threshold"]), RAD_ORDER.index(P[w]["radius"]), w))
    fig, axes = plt.subplots(2, 1, figsize=(WIDTH_IN, 7.6), sharex=True)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.9, bottom=0.2, hspace=0.18)
    lines = [f"x order (threshold, radius, id): " + ", ".join(f"{w}({THR_LABEL[P[w]['threshold']]},{RAD_LABEL[P[w]['radius']]})" for w in order)]
    x = np.arange(len(order))
    for ax, tag, name in zip(axes, ["qwen3b", "qwen7b"], ["3B", "7B"]):
        C = numbers_per_phrasing(tag)
        bottom = np.zeros(len(order))
        for k in NUMS + ["other"]:
            v = np.array([C[w][k] for w in order])
            ax.bar(x, v, bottom=bottom, color=COL[k], width=0.78, label=k, edgecolor="white", linewidth=0.6)
            bottom += v
        ax.set_ylim(0, 30); ax.set_yticks([0, 10, 20, 30]); ax.set_ylabel(f"{name}\nsamples")
        lines.append(f"{name} per phrasing (1/3, 1/2, 1/4, other): " + "; ".join(
            f"{w}: {C[w]['1/3']},{C[w]['1/2']},{C[w]['1/4']},{C[w]['other']}" for w in order))
    axes[0].legend(ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.02), frameon=False)
    ax = axes[1]
    ax.set_xticks(x); ax.set_xticklabels([str(w) for w in order])
    trans = matplotlib.transforms.blended_transform_factory(ax.transData, ax.transAxes)
    # radius subgroups and threshold groups below the ticks
    for thr in THR_ORDER:
        idx = [i for i, w in enumerate(order) if P[w]["threshold"] == thr]
        for rad in RAD_ORDER:
            sub = [i for i in idx if P[order[i]]["radius"] == rad]
            if sub:
                ax.text(np.mean(sub), -0.25, RAD_LABEL[rad], transform=trans, ha="center", va="top", fontsize=12, color="#555555")
        ax.text(np.mean(idx), -0.42, THR_LABEL[thr], transform=trans, ha="center", va="top", fontsize=16)
        ax.annotate("", xy=(idx[0] - 0.4, -0.38), xytext=(idx[-1] + 0.4, -0.38), xycoords=trans, textcoords=trans,
                    arrowprops=dict(arrowstyle="-", color="#777777", lw=1.4))
        if thr != THR_ORDER[-1]:
            for a in axes:
                a.axvline(idx[-1] + 0.5, color="#cccccc", lw=1.2, zorder=0)
    ax.text(-0.01, -0.035, "phrasing", transform=ax.transAxes, ha="right", va="top", fontsize=13, color="#555555")
    save(fig, "which")
    note("which", lines)
    CAPTIONS["which"] = ("Which number each model gives on each phrasing of the neutral problem (30 samples per phrasing, "
                         "temperature 0.7, label = final number). Phrasings are grouped by how the threshold is stated "
                         "(triangle side, r√3, or a number) and by radius (\"r\": radius not given).")


# ---------------------------------------------------------------- 4 how
def fig_how():
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 6.2))
    fig.subplots_adjust(left=0.1, right=0.72, top=0.97, bottom=0.17)
    lines = []
    xs, labels = [], []
    for i, num in enumerate(NUMS):
        for j, (tag, name) in enumerate([("qwen3b", "3B"), ("qwen7b", "7B")]):
            x = i * 2.6 + j * 1.0
            J = [r for r in judge(tag) if r["final_number"] == num]
            der = Counter(r["variable"] for r in J if r["derived_or_recalled"] == "derived")
            rec = Counter(r["variable"] for r in J if r["derived_or_recalled"] == "recalled")
            b = 0
            for var in ["angle at the center", "distance from the center", "midpoint in the disk"] + sorted(set(der) - set(VAR2NUM)):
                if der.get(var):
                    ax.bar(x, der[var], bottom=b, width=0.85, color=COL[VAR2NUM.get(var, "other")], edgecolor="white", lw=0.6)
                    b += der[var]
            nrec = sum(rec.values())
            ax.bar(x, nrec, bottom=b, width=0.85, **recalled_patch_kw(num))
            ax.text(x, b + nrec + 3, f"{b}/{nrec}", ha="center", va="bottom", fontsize=12)
            xs.append(x); labels.append(name)
            lines.append(f"{name} {num}: derived {b} (" + ", ".join(f"{VAR_SHORT.get(k, k)} {v}" for k, v in der.items()) +
                         f"); recalled {nrec} (" + ", ".join(f"{VAR_SHORT.get(k, k)} {v}" for k, v in rec.most_common()) + ")")
        ax.text(i * 2.6 + 0.5, -0.13, num, transform=matplotlib.transforms.blended_transform_factory(ax.transData, ax.transAxes),
                ha="center", va="top", fontsize=20, color=COL[num], fontweight="bold")
    ax.set_xticks(xs); ax.set_xticklabels(labels)
    ax.set_ylabel("answers ending in that number")
    from matplotlib.patches import Patch
    handles = [Patch(color=COL["1/3"], label="derived: angle"), Patch(color=COL["1/2"], label="derived: distance"),
               Patch(color=COL["1/4"], label="derived: midpoint"),
               Patch(**recalled_patch_kw("other"), label="recalled\n(hatched, in the\nnumber's color)")]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False)
    ax.text(1.03, 0.52, "bar labels: derived/recalled", transform=ax.transAxes, fontsize=12, color="#555555")
    save(fig, "how")
    note("how", lines)
    CAPTIONS["how"] = ("How the neutral answers ending in 1/3, 1/2 or 1/4 got there, by hand judgment. Solid: derived "
                       "(the written steps produce the number), colored by the variable treated as evenly spread; every "
                       "derived 1/3 uses the angle, every derived 1/2 the distance, every derived 1/4 the midpoint, so the "
                       "colors match the numbers. Hatched: recalled (the working gives something else, or the number is "
                       "just stated). 3B: 361 answers; 7B: 400.")


# ---------------------------------------------------------------- 5 famous number
def fig_famous():
    P = neutral_prompts()
    fig = plt.figure(figsize=(WIDTH_IN, 6.4))
    ax = fig.add_axes([0.08, 0.14, 0.33, 0.80])
    lines = []
    for j, (tag, name, col) in enumerate([("qwen3b", "3B", "#9fb6d8"), ("qwen7b", "7B", "#3b3b3b")]):
        J = judge(tag)
        for i, thr in enumerate(THR_ORDER):
            S = [r for r in J if P[r["wording_id"]]["threshold"] == thr]
            d = sum(r["derived_or_recalled"] == "derived" for r in S)
            share = d / len(S)
            x = i + (j - 0.5) * 0.38
            ax.bar(x, 100 * share, width=0.36, color=col, label=name if i == 0 else None)
            ax.text(x, 100 * share + 1.5, f"{100 * share:.0f}%", ha="center", va="bottom", fontsize=12)
            ax.text(x, 3, f"{d}/\n{len(S)}", ha="center", va="bottom", fontsize=10, color="white" if j else INK)
            lines.append(f"{name} {THR_LABEL[thr]}: derived {d}/{len(S)} = {100 * share:.0f}%")
    ax.set_xticks(range(3)); ax.set_xticklabels([THR_LABEL[t] for t in THR_ORDER])
    ax.set_ylim(0, 115); ax.set_yticks([0, 25, 50, 75, 100]); ax.set_ylabel("derived share (%)")
    ax.set_xlabel("threshold phrasing")
    ax.legend(loc="upper left", frameon=False, ncol=2)
    # right: one recalled 1/3
    rows = {(r["wording_id"], r["sample"]): r for r in read_jsonl(RESULTS / "s1" / "neutral_qwen7b.jsonl") if r.get("kind") == "answer"}
    ans = rows[RECALLED_EXAMPLE]["answer"].split("\n")
    tx = fig.add_axes([0.46, 0.02, 0.53, 0.96]); tx.axis("off"); tx.set_xlim(0, 1); tx.set_ylim(0, 1)
    tx.text(0.0, 0.99, f"7B, phrasing {RECALLED_EXAMPLE[0]}, sample {RECALLED_EXAMPLE[1]} (shortened)", fontsize=12,
            color="#555555", va="top", style="italic")
    y = 0.93
    shown = []
    for li in RECALLED_LINES:
        if li is None:
            tx.text(0.0, y, "…", fontsize=11, family="monospace", va="top", color="#888888"); y -= 0.038; continue
        mark = RECALLED_MARK.get(li)
        wrapped = textwrap.wrap(ans[li], 56) or [""]
        for w in wrapped:
            kw = {}
            if mark == "other":
                kw = dict(bbox=dict(boxstyle="square,pad=0.12", fc="#f6d7d7", ec="none"))
            elif mark == "boxed":
                kw = dict(bbox=dict(boxstyle="square,pad=0.12", fc=matplotlib.colors.to_rgba(COL["1/3"], 0.3), ec="none"))
            tx.text(0.0, y, esc(w), fontsize=11, family="monospace", va="top", **kw)
            y -= 0.038
        shown.append(li)
    tx.text(0.0, y - 0.01, "red: the working computes 2/3     blue: the boxed answer is 1/3", fontsize=11, color="#555555", va="top")
    save(fig, "famous_number")
    lines.append(f"right panel: 7B phrasing {RECALLED_EXAMPLE[0]} sample {RECALLED_EXAMPLE[1]}, answer lines {shown}; "
                 f"highlighted line 26 (computes 2/3) and line 29 (boxed 1/3)")
    note("famous number", lines)
    CAPTIONS["famous_number"] = ("Left: share of hand-judged answers whose steps actually produce their number, by how the "
                                 "threshold is phrased. Right: a recalled 1/3 from the 7B (real answer, lines removed where "
                                 "marked …): the working gives 2/3, the boxed answer is the famous 1/3.")


# ---------------------------------------------------------------- 6 where we look
def fig_where():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
    meta = {(r["wording_id"], r["sample"]): r for r in read_jsonl(RESULTS / "s2" / "acts_word_qwen7b_meta.jsonl")[1:]}
    m = meta[STRIP_EXAMPLE]
    rows = {(r["wording_id"], r["sample"]): r for r in read_jsonl(RESULTS / "s1" / "neutral_qwen7b.jsonl") if r.get("kind") == "answer"}
    ans = rows[STRIP_EXAMPLE]["answer"]
    a_ids = tok(ans, add_special_tokens=False).input_ids
    p_ids = tok(chat_prompt(tok, m["prompt"]), add_special_tokens=False).input_ids
    t = m["word_tok"]
    w_end = t + len(tok(" " + m["word_match"], add_special_tokens=False).input_ids)  # tokens of the branch word
    toks = [("p", i, tok.decode([p_ids[i]])) for i in range(len(p_ids) - 4, len(p_ids))]
    toks += [("a", i, tok.decode([a_ids[i]])) for i in range(0, min(w_end + 3, len(a_ids)))]
    fig = plt.figure(figsize=(WIDTH_IN, 7.4 * 0.70))
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.98]); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(30, 100)
    x, y, row_h, cw = 1.0, 88.0, 12.0, 1.02
    pos = {}
    for kind, i, s in toks:
        disp = s.replace("\n", "↵").replace(" ", "·") if s.strip() == "" else s.replace("\n", "↵")
        w = max(2.2, cw * len(disp) + 1.0)
        if x + w > 99:
            x, y = 1.0, y - row_h
        fc = "#f2f2f2" if kind == "p" else "white"
        if kind == "a" and t <= i < w_end:
            fc = matplotlib.colors.to_rgba(COL["1/2"], 0.45)
        ax.add_patch(Rectangle((x, y - 3.2), w - 0.3, 6.4, fc=fc, ec="#c8c8c8", lw=0.8))
        ax.text(x + (w - 0.3) / 2, y, esc(disp), ha="center", va="center", fontsize=11.5, family="DejaVu Sans")
        pos[(kind, i)] = (x, y, w - 0.3)
        x += w
    lp = pos[("p", len(p_ids) - 1)]
    ax.annotate("last prompt token", xy=(lp[0] + lp[2] / 2, lp[1] + 3.3), xytext=(lp[0] + lp[2] / 2 + 6, lp[1] + 8.5),
                fontsize=12, arrowprops=dict(arrowstyle="->", color=INK), ha="left")
    # first-60 bracket: per row segments under tokens 0..59
    segs = defaultdict(list)
    for i in range(60):
        px, py, pw = pos[("a", i)]
        segs[py].append((px, px + pw))
    for py, ss in segs.items():
        x0, x1 = min(s[0] for s in ss), max(s[1] for s in ss)
        ax.plot([x0, x1], [py - 4.4, py - 4.4], color="#555555", lw=2.2)
        ax.plot([x0, x0], [py - 4.4, py - 3.6], color="#555555", lw=2.2)
        ax.plot([x1, x1], [py - 4.4, py - 3.6], color="#555555", lw=2.2)
    last_py = min(segs)
    ax.text(max(s[1] for s in segs[last_py]) + 1, last_py - 5.2, "first 60 answer tokens", fontsize=12, color="#555555", va="center")
    for k in (30, 10, 5, 1):
        px, py, pw = pos[("a", t - k)]
        ax.plot([px + pw / 2, px + pw / 2], [py + 3.3, py + 4.8], color=INK, lw=1.8)
        ax.text(px + pw / 2, py + 5.0, str(k), ha="center", va="bottom", fontsize=12, fontweight="bold")
    bx, by, bw = pos[("a", t)]
    ax.text(bx, by - 6.0, "branch word", fontsize=12, color=COL["1/2"], fontweight="bold", va="top")
    save(fig, "where_we_look")
    note("where we look", [f"7B phrasing {STRIP_EXAMPLE[0]} sample {STRIP_EXAMPLE[1]} (final number {m['final_number']}, derived); "
                           f"prompt {len(p_ids)} tokens, last 4 shown; answer tokens 0–{min(w_end + 3, len(a_ids)) - 1} shown; "
                           f"branch word \"{m['word_match']}\" at answer token {t} (tokens {t}–{w_end - 1}); "
                           f"ticks at answer tokens {t - 30}, {t - 10}, {t - 5}, {t - 1}; first-60 bracket over tokens 0–59",
                           "median branch-word position over the 342 answers: token 110"])
    CAPTIONS["where_we_look"] = (f"Where the probes look, on one real 7B answer (phrasing {STRIP_EXAMPLE[0]}, sample "
                                 f"{STRIP_EXAMPLE[1]}). Grey: the end of the prompt; the last prompt token is the reading "
                                 f"probe's position. Bracket: the first 60 answer tokens averaged by the window probe. "
                                 f"Highlighted: the first word that names the variable (the branch word, here at token {t}); "
                                 f"ticks mark positions 30, 10, 5 and 1 tokens before it. This answer was chosen for fit; "
                                 f"the branch word usually comes around token 110.")


# ---------------------------------------------------------------- 7 when
def fig_when():
    W = json.loads((RESULTS / "s2" / "word_probe_qwen7b.json").read_text(encoding="utf-8"))
    L = "22"
    ks = W["offsets"]
    probe = [100 * W["curves"]["main"][str(k)][L]["bal"] for k in ks]
    words = [100 * W["words"][str(k)]["prompt_plus_answer_text"]["bal"] for k in ks]
    within = [100 * W["best_rerun"][str(k)]["null_within"]["bal_p95"] for k in ks]
    assert W["best_layer"] == 22
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 6.0))
    fig.subplots_adjust(left=0.1, right=0.97, top=0.97, bottom=0.14)
    ax.plot(ks, probe, "-o", color=INK, lw=3, ms=8, label="probe on the residual stream (layer 22)")
    ax.plot(ks, words, "-s", color="#c0504d", lw=2.4, ms=7, label="words only (prompt + answer text so far)")
    ax.plot(ks, within, "-^", color="#7f7f7f", lw=2.4, ms=7, label="labels shuffled within phrasing, 95th pct")
    ax.axhline(100 / 3, ls="--", color="#999999", lw=1.6)
    ax.text(29.5, 34.5, "chance 33%", color="#777777", fontsize=13)
    ax.set_xlim(31, -1); ax.set_xticks(ks)
    ax.set_ylim(25, 90)
    ax.set_xlabel("tokens before the branch word")
    ax.set_ylabel("balanced accuracy (%)")
    ax.legend(loc="upper left", frameon=False)
    save(fig, "when")
    note("when", [f"x (tokens before the branch word): {ks}",
                  "probe, layer 22, balanced accuracy (%): " + ", ".join(f"{v:.1f}" for v in probe),
                  "words only, prompt + answer text up to that point (%): " + ", ".join(f"{v:.1f}" for v in words),
                  "within-phrasing shuffle, 95th percentile, 50 shuffles (%): " + ", ".join(f"{v:.1f}" for v in within),
                  "chance: 33.3%", f"n per offset: " + ", ".join(str(W['curves']['main'][str(k)][L]['n']) for k in ks)])
    CAPTIONS["when"] = ("When the final number becomes readable in the 7B's answer. x: position, in tokens before the "
                        "first word that names the variable; y: balanced accuracy of a linear probe for the final number "
                        "(1/3, 1/2, 1/4), test phrasings unseen in training. Black: probe on the residual stream at layer 22. "
                        "Red: a classifier on the words alone. Grey: what shuffling labels within each phrasing reaches "
                        "(95th percentile of 50 shuffles), the bar for reading more than the phrasing.")


def main():
    for f in (fig_header, fig_phrasings, fig_which, fig_how, fig_famous, fig_where, fig_when):
        f()
    (OUT / "numbers.md").write_text("# Numbers drawn in each figure\n\n" + "\n".join(NUMBERS) + "\n", encoding="utf-8")
    (OUT / "captions.md").write_text("# Figure captions\n\n" + "\n\n".join(f"**{k}.** {v}" for k, v in CAPTIONS.items()) + "\n",
                                     encoding="utf-8")
    print("\n".join(NUMBERS))


if __name__ == "__main__":
    main()
