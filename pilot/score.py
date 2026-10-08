"""Score a model answer to a Bertrand prompt.

Primary label = the final number: 1/3 -> A (endpoints), 1/2 -> B (radial), 1/4 -> C (midpoint),
anything else -> "other", no number -> "none", several canonical numbers with no clear final -> "multiple".
Secondary label = method keywords in the text (first approach mentioned). Run this file to self-test.
"""
import re

CANON = {"A": 1 / 3, "B": 1 / 2, "C": 1 / 4}
TOL = 0.011
WORDS = {"one third": 1 / 3, "one-third": 1 / 3, "a third": 1 / 3,
         "one half": 1 / 2, "one-half": 1 / 2, "a half": 1 / 2,
         "one quarter": 1 / 4, "one-quarter": 1 / 4, "a quarter": 1 / 4, "one fourth": 1 / 4, "one-fourth": 1 / 4}

NUM_RE = re.compile(
    r"\\[dt]?frac\{(?P<fn>\d+)\}\{(?P<fd>\d+)\}"
    r"|(?P<n>\d+)\s*/\s*(?P<d>\d+)"
    r"|(?P<pct>\d+(?:\.\d+)?)\s*%"
    r"|(?P<dec>\d*\.\d+)"
    r"|(?P<word>" + "|".join(re.escape(w) for w in WORDS) + r")"
    r"|(?<![\d.])(?P<int>[01])(?!\d|\.\d|/)",  # bare 0 or 1 (a probability can be exactly these)
    re.IGNORECASE)
BOXED_RE = re.compile(r"\\boxed\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}")
CUE_WORD = re.compile(r"probab|chance|answer|likelihood|odds|\bP\s*[=(]", re.I)
CONNECTOR = re.compile(r"(?:\bis|=|equals|\bbe|:|≈|approximately|about|roughly|\bof|probability|chance|answer|therefore|thus|so|get|gives|obtain)\s*$", re.I)
WRAP = re.compile(r"[\s$\\()\[\]{},]+$")
SENTENCE_END = re.compile(r"[.!?](?:\s|$)|\n")
PARADOX_RE = re.compile(r"bertrand|depends on (?:how|the|which|what)|ambiguous|ill[- ]posed|not well[- ]defined|different (?:answers|methods|interpretations)|paradox", re.I)

METHOD_RE = {
    "A": re.compile(r"two (?:\w+ )?(?:\w+ )?points|two endpoints|two angles|each endpoint|endpoints (?:are|be) (?:chosen|picked|selected|uniform)|two (?:random )?(?:directions|spots|locations)", re.I),
    "B": re.compile(r"random radius|distance (?:from|to|of) the (?:cent(?:er|re)|chord)|perpendicular to (?:the|a|this|that) radius|along (?:a|the|this) radius|random diameter|at a (?:random )?distance|distance d\b", re.I),
    "C": re.compile(r"mid-?point|uniform(?:ly)?(?: distributed)? (?:in|over|inside|within|throughout) the (?:disk|disc|circle|area|interior)|random point (?:in|inside|within) the (?:disk|disc|circle|interior)|bisect", re.I),
}


def _val(m):
    if m.group("fn"):
        return int(m.group("fn")) / int(m.group("fd")) if int(m.group("fd")) else None
    if m.group("n"):
        return int(m.group("n")) / int(m.group("d")) if int(m.group("d")) else None
    if m.group("pct"):
        return float(m.group("pct")) / 100
    if m.group("dec"):
        return float(m.group("dec"))
    if m.group("int"):
        return float(m.group("int"))
    return WORDS[m.group("word").lower()]


def numbers(text):
    out = []
    for m in NUM_RE.finditer(text):
        v = _val(m)
        if v is not None:
            out.append((v, m.start(), m.end()))
    return out


def to_approach(v):
    if v is None:
        return "none"
    for a, c in CANON.items():
        if abs(v - c) <= TOL:
            return a
    return "other"


def _cued(text, start):
    pre = text[max(0, start - 120):start]
    return bool(CUE_WORD.search(pre)) and bool(CONNECTOR.search(WRAP.sub("", pre)[-40:]))


def _canonical_set(nums):
    return {to_approach(v) for v, _, _ in nums} & set(CANON)


def final_number(text):
    """-> (value or None, how) with how in boxed / boxed_other / cued / fallback / none / multiple.
    A boxed answer is always taken as the final answer, even when it is not a parseable number."""
    boxed = BOXED_RE.findall(text)
    if boxed:
        nums = numbers(boxed[-1])
        if len(_canonical_set(nums)) >= 2:
            return None, "multiple"
        if nums:
            return nums[-1][0], "boxed"
        return None, "boxed_other"
    nums = numbers(text)
    cued = [n for n in nums if _cued(text, n[1])]
    if cued:
        v, _, end = cued[-1]
        m = SENTENCE_END.search(text, end)
        rest = text[end:m.start() if m else len(text)]
        others = _canonical_set(numbers(rest)) - {to_approach(v)}
        return (None, "multiple") if others else (v, "cued")
    if nums:
        canon = _canonical_set(nums)
        if len(canon) >= 2:
            return None, "multiple"
        return nums[-1][0], "fallback"
    return None, "none"


def method_from_text(text):
    hits = {}
    for a, rx in METHOD_RE.items():
        m = rx.search(text)
        if m:
            hits[a] = m.start()
    if not hits:
        return "none", []
    first = min(hits, key=hits.get)
    return first, sorted(hits)


def score(text):
    v, how = final_number(text)
    by_number = {"multiple": "multiple", "boxed_other": "other"}.get(how) or to_approach(v)
    by_text, mentioned = method_from_text(text)
    return {
        "final_value": None if v is None else round(v, 4),
        "final_how": how,
        "approach_number": by_number,
        "approach_text": by_text,
        "methods_mentioned": mentioned,
        "agree": by_number == by_text if by_number in CANON and by_text in CANON else None,
        "mentions_paradox": bool(PARADOX_RE.search(text)),
        "n_canonical_mentioned": len(_canonical_set(numbers(text))),
    }


TESTS = [
    ("The probability is 1/3.", "A"),
    ("Therefore the answer is \\boxed{\\frac{1}{2}}.", "B"),
    ("Therefore P = 0.25.", "C"),
    ("It could be 1/3 or 1/2 under other conventions. With our method the answer is 1/4.", "C"),
    ("So the probability is 33.3%.", "A"),
    ("The probability is approximately 0.333.", "A"),
    ("The chance is one third.", "A"),
    ("The probability is 2/3.", "other"),
    ("This is Bertrand's paradox; the answer depends on the method: 1/2, 1/3 or 1/4.", "multiple"),
    ("We cannot say without more information.", "none"),
    ("\\[ P = \\dfrac{1}{4} \\]", "C"),
    ("so the answer is 1/3 for a circle of radius 2.", "A"),
    ("The probability that the chord is longer is 50%.", "B"),
    ("P(L > s) = 1 - 1/2 = 1/2", "B"),
    ("Thus the probability is $\\frac{1}{3}$.", "A"),
    ("The desired probability is \\( \\frac{1}{4} \\).", "C"),
    ("The side is 2√3 ≈ 3.46. Hence the probability equals 1/3.", "A"),
    ("The chord is longer when the midpoint is within r/2 of the center, so the probability is (1/2)^2 = 1/4.", "C"),
    ("Pick two random points on the circle. The arc condition gives probability 1/3.", "A"),
    ("we have 0.5 as the answer", "fallback-B"),
    ("Using L = 2R sin(θ/2) with sin(30°) = \\frac{1}{2}, no chord is longer, so P = 0. Thus the answer is \\(\\boxed{0}\\).", "other"),
    ("The probability is 1.", "other"),
    ("So the answer is \\boxed{\\frac{\\sqrt{3}}{2}}.", "other"),
    ("Hence P = \\boxed{\\dfrac{1}{3}}.", "A"),
    ("The distance is uniform on [0, r]. The chord is longer when d < r/2, so the probability is 1/2.", "B"),
]


def self_test():
    bad = 0
    for text, want in TESTS:
        s = score(text)
        got = s["approach_number"]
        want_how = None
        if "-" in want:
            want_how, want = want.split("-")
        ok = got == want and (want_how is None or s["final_how"] == want_how)
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} want={want:8s} got={got:8s} how={s['final_how']:8s} text={s['approach_text']:5s} | {text[:70]}")
    print(f"{len(TESTS) - bad}/{len(TESTS)} passed")
    return bad == 0


if __name__ == "__main__":
    raise SystemExit(0 if self_test() else 1)
