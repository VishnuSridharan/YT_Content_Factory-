"""Long-form narrated case-study format: beat sheet, word budgets, and a script validator.

The Shorts pipeline optimizes one idea in 50 seconds. This module models the
*other* format on the channel: an 8-14 minute explainer narrated by a human,
built like a business case study — shock stat, contradiction, escalating acts,
mechanism reveal, counter-view, portable framework, callback.

Nothing here calls an LLM. The beat sheet is a plan you can write against by
hand, and `validate_script` is a mechanical QA pass over the finished words:
it measures the things that actually correlate with a narration holding
attention (sentence length, number density, direct address, pattern
interrupts, callback) instead of asking a model whether the script is "good".

See docs/NARRATION_PLAYBOOK.md for the reasoning behind each beat.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A relaxed, clearly-articulated narration runs ~140 words per minute. Faster than
# ~165 and a listener loses numbers; slower than ~120 and the middle sags.
WORDS_PER_MINUTE = 140


@dataclass(frozen=True)
class Beat:
    """One structural unit of the script."""

    key: str
    name: str
    purpose: str  # the job this beat does on the listener
    share: float  # fraction of the total word budget
    guidance: str  # how to write it


# Shares sum to 1.0. The three acts are separate beats so an outline can name a
# different concrete event in each one instead of producing a single mushy middle.
BEAT_SHEET: tuple[Beat, ...] = (
    Beat(
        key="cold_open",
        name="Cold open",
        purpose="Open an information gap in the first 10 seconds.",
        share=0.035,
        guidance=(
            "One absurd, specific, verifiable fact — a number, a date, or a contrast. "
            "No greeting, no channel name, no 'in this video'. The listener must feel "
            "they walked in on the middle of something."
        ),
    ),
    Beat(
        key="gap",
        name="The contradiction",
        purpose="Convert the fact into a question the listener now needs answered.",
        share=0.05,
        guidance=(
            "State why the cold-open fact should be impossible. Two forces that cannot "
            "both be true. End on the question the rest of the video answers."
        ),
    ),
    Beat(
        key="promise",
        name="Promise",
        purpose="Pre-load three open loops so the listener stays for all three.",
        share=0.035,
        guidance=(
            "Name exactly what they will understand by the end, as three items. "
            "Concrete nouns, not 'we will explore'. This is the only self-referential "
            "part of the script; keep it under 15 seconds."
        ),
    ),
    Beat(
        key="ground_zero",
        name="Ground zero",
        purpose="Give the abstraction a character, a place and a year.",
        share=0.14,
        guidance=(
            "Start the story before the problem existed. Name a person, a company or a "
            "team. Year and place in the first sentence. The listener must be able to "
            "picture a room."
        ),
    ),
    Beat(
        key="act_one",
        name="Act 1 — the move",
        purpose="First escalation.",
        share=0.13,
        guidance=(
            "Setup, obstacle, the decision taken, the measurable result. Close on a "
            "sentence that makes the next problem inevitable."
        ),
    ),
    Beat(
        key="act_two",
        name="Act 2 — the cost",
        purpose="Second escalation; raise the stakes.",
        share=0.13,
        guidance=(
            "What the Act 1 decision broke. Bigger number, wider blast radius. "
            "This is where most listeners drop — put your strongest concrete detail here."
        ),
    ),
    Beat(
        key="act_three",
        name="Act 3 — the breaking point",
        purpose="Third escalation; force the question to a head.",
        share=0.13,
        guidance=(
            "The moment the old approach visibly fails. End on the question the "
            "mechanism beat is about to answer."
        ),
    ),
    Beat(
        key="mechanism",
        name="Mechanism reveal",
        purpose="Pay off the curiosity gap — the satisfaction core of the video.",
        share=0.10,
        guidance=(
            "How it actually works, in plain language, with one everyday analogy. "
            "This is the part people re-watch and quote. Slow down: short sentences, "
            "one idea per sentence, arithmetic the listener can do in their head."
        ),
    ),
    Beat(
        key="counter",
        name="Counter-view",
        purpose="Buy credibility by arguing against your own conclusion.",
        share=0.10,
        guidance=(
            "The strongest honest objection, stated fairly, then answered — or conceded. "
            "Analysis without this beat reads as hype and loses the technical audience."
        ),
    ),
    Beat(
        key="framework",
        name="Portable framework",
        purpose="Give the listener something to repeat tomorrow.",
        share=0.09,
        guidance=(
            "Name the lesson — two or three words the listener can say out loud. "
            "Then two or three numbered rules that apply beyond this one story. "
            "This beat is what gets the video shared."
        ),
    ),
    Beat(
        key="close",
        name="Callback close",
        purpose="Close the loop opened in the cold open; leave one live question.",
        share=0.06,
        guidance=(
            "Return to the exact number or image from the cold open and reread it with "
            "everything the listener now knows. End on a forward question, not a summary."
        ),
    ),
)

BEATS_BY_KEY = {b.key: b for b in BEAT_SHEET}


@dataclass(frozen=True)
class BeatPlan:
    beat: Beat
    words: int
    start_s: int
    end_s: int

    @property
    def timecode(self) -> str:
        return (
            f"{self.start_s // 60}:{self.start_s % 60:02d}-"
            f"{self.end_s // 60}:{self.end_s % 60:02d}"
        )


def plan_beats(minutes: float, wpm: int = WORDS_PER_MINUTE) -> list[BeatPlan]:
    """Word and time budget per beat for a target runtime."""
    total_words = int(minutes * wpm)
    plans: list[BeatPlan] = []
    cursor = 0.0
    for beat in BEAT_SHEET:
        words = round(total_words * beat.share)
        seconds = words / wpm * 60
        plans.append(BeatPlan(beat, words, int(cursor), int(cursor + seconds)))
        cursor += seconds
    return plans


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

# Openers that tell the listener nothing and cost the first five seconds.
BANNED_OPENERS = (
    r"^\s*(hi|hey|hello|welcome)\b",
    r"^\s*in this (video|episode)\b",
    r"^\s*today (we|i)('| a)?\b",
    r"^\s*so\b.{0,30}\btoday\b",
    r"^\s*let'?s (talk|dive|get started)\b",
    r"^\s*have you ever (wondered|thought)\b",
)

# Pattern interrupts. One roughly every 90 seconds resets a drifting listener.
INTERRUPT_MARKERS = (
    "but here",
    "but this",
    "but that",
    "here is the",
    "here's the",
    "now here",
    "and this is where",
    "except",
    "the problem is",
    "the catch",
    "the twist",
    "which brings us",
    "so what changed",
    "and then",
)

# Terms that mean nothing to a general audience unless glossed on the spot.
JARGON = (
    "agentic",
    "agent",
    "llm",
    "inference",
    "token",
    "context window",
    "fine-tune",
    "fine tune",
    "rag",
    "embedding",
    "orchestration",
    "latency",
    "throughput",
    "api",
    "gpu",
    "benchmark",
    "parameter",
    "multimodal",
    "gdp",
    "tariff",
    "arbitrage",
    "capex",
)

GLOSS_MARKERS = (
    "means",
    "meaning",
    "in simple",
    "simply",
    "think of",
    "imagine",
    "that is",
    "in other words",
    "basically",
    "put simply",
    "which is just",
    "i.e.",
    "— a ",
    "- a ",
)


@dataclass(frozen=True)
class Finding:
    level: str  # "error" | "warn"
    code: str
    message: str


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text.strip()))
    return [p.strip() for p in parts if p.strip()]


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9'’%$₹.-]+", text)


# Spoken narration writes quantities as words ("ninety-five percent", "forty minutes"),
# so digit-matching alone would score a perfectly specific script as vague.
NUMBER_WORDS = frozenset(
    """zero one two three four five six seven eight nine ten eleven twelve thirteen
    fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty
    sixty seventy eighty ninety hundred hundreds thousand thousands lakh crore million
    millions billion billions trillion percent half twice double triple dozen""".split()
)


def _is_numeric(token: str) -> bool:
    """True for '2024', '40%', '$3', 'ninety-five', 'forty-two'."""
    t = token.lower().strip(".,'’")
    if re.search(r"\d", t):
        return True
    # hyphenated compounds: every part must be a number word ("ninety-five", but not
    # "nearly-perfect")
    parts = [p for p in t.split("-") if p]
    return bool(parts) and all(p in NUMBER_WORDS for p in parts)


_STOPWORDS = frozenset(
    """a an and are as at be been but by can did do does for from had has have how if in
    into is it its of on or that the their them then there these they this to was were
    what when where which who why will with you your our we us not no than then more most
    one two three""".split()
)


def _content_words(text: str) -> set[str]:
    return {
        w.lower().strip(".,'’")
        for w in _words(text)
        if len(w) > 3 and w.lower() not in _STOPWORDS
    }


def script_metrics(text: str) -> dict:
    """Raw measurements, independent of any threshold."""
    sents = _sentences(text)
    words = _words(text)
    n_words = len(words)
    lens = [len(_words(s)) for s in sents] or [0]
    lower = text.lower()
    numeric = sum(1 for w in words if _is_numeric(w))
    you = len(re.findall(r"\b(you|your|you're|yourself)\b", lower))
    interrupts = sum(lower.count(m) for m in INTERRUPT_MARKERS)
    return {
        "words": n_words,
        "sentences": len(sents),
        "runtime_minutes": round(n_words / WORDS_PER_MINUTE, 1),
        "avg_sentence_words": round(sum(lens) / len(lens), 1),
        "longest_sentence_words": max(lens),
        "numbers_per_100_words": round(numeric / max(n_words, 1) * 100, 1),
        "you_per_100_words": round(you / max(n_words, 1) * 100, 1),
        "pattern_interrupts": interrupts,
    }


def validate_script(text: str, target_minutes: float = 10.0) -> tuple[dict, list[Finding]]:
    """Mechanical QA over a finished narration script.

    Returns (metrics, findings). `error` findings mean the script breaks the
    format; `warn` findings are worth a human look but can be deliberate.
    """
    m = script_metrics(text)
    out: list[Finding] = []
    sents = _sentences(text)
    words = _words(text)
    if not sents:
        return m, [Finding("error", "empty", "Script is empty.")]

    target_words = target_minutes * WORDS_PER_MINUTE
    if m["words"] < target_words * 0.85 or m["words"] > target_words * 1.15:
        out.append(
            Finding(
                "warn",
                "length",
                f"{m['words']} words ≈ {m['runtime_minutes']} min; target "
                f"{target_minutes} min (±15% = {int(target_words * 0.85)}-"
                f"{int(target_words * 1.15)} words).",
            )
        )

    first = sents[0]
    for pattern in BANNED_OPENERS:
        if re.search(pattern, first, re.IGNORECASE):
            out.append(
                Finding("error", "weak_opener", f"Cold open is a throat-clear: {first[:80]!r}")
            )
            break
    if len(_words(first)) > 25:
        out.append(
            Finding(
                "warn",
                "opener_length",
                f"First sentence is {len(_words(first))} words. Under 25 lands harder.",
            )
        )
    if not any(_is_numeric(w) for w in words[:40]):
        out.append(
            Finding(
                "error",
                "no_hook_number",
                "No number in the first 40 words. The gap needs something countable.",
            )
        )

    if m["numbers_per_100_words"] < 1.0:
        out.append(
            Finding(
                "warn",
                "thin_specifics",
                f"{m['numbers_per_100_words']} numbers per 100 words. Aim for 1.5+ — "
                "specifics are what separate analysis from opinion.",
            )
        )
    if m["avg_sentence_words"] > 17:
        out.append(
            Finding(
                "warn",
                "long_sentences",
                f"Average sentence {m['avg_sentence_words']} words. Spoken narration "
                "reads best at 11-15.",
            )
        )
    for s in sents:
        if len(_words(s)) > 38:
            out.append(
                Finding("warn", "run_on", f"{len(_words(s))}-word sentence: {s[:90]}…")
            )
            break
    if m["you_per_100_words"] < 0.5:
        out.append(
            Finding(
                "warn",
                "no_direct_address",
                "Almost no 'you'. Direct address every ~60 words keeps it a conversation.",
            )
        )
    expected_interrupts = max(2, int(target_minutes / 1.5))
    if m["pattern_interrupts"] < expected_interrupts:
        out.append(
            Finding(
                "warn",
                "few_interrupts",
                f"{m['pattern_interrupts']} pattern interrupts; want ~{expected_interrupts} "
                "(one per 90 seconds) to reset drifting attention.",
            )
        )

    ungloss = _ungloss_jargon(sents)
    if ungloss:
        out.append(
            Finding(
                "warn",
                "unglossed_jargon",
                "Jargon used without a plain-language gloss nearby: " + ", ".join(sorted(ungloss)),
            )
        )

    # Windows must not overlap, or a short script "calls back" to itself.
    open_n = min(45, max(8, len(words) // 3))
    close_n = min(70, max(10, len(words) // 3))
    open_words = _content_words(" ".join(words[:open_n]))
    close_words = _content_words(" ".join(words[-close_n:]))
    if not (open_words & close_words):
        out.append(
            Finding(
                "warn",
                "no_callback",
                "The close shares no specific word with the cold open. Return to the "
                "opening number so the loop shuts.",
            )
        )
    return m, out


def _ungloss_jargon(sents: list[str]) -> set[str]:
    """Jargon whose FIRST use has no plain-language gloss in that or the next sentence."""
    seen: set[str] = set()
    flagged: set[str] = set()
    for i, s in enumerate(sents):
        window = (s + " " + (sents[i + 1] if i + 1 < len(sents) else "")).lower()
        for term in JARGON:
            if term in seen:
                continue
            if re.search(rf"\b{re.escape(term)}\b", s, re.IGNORECASE):
                seen.add(term)
                if not any(g in window for g in GLOSS_MARKERS):
                    flagged.add(term)
    return flagged


def format_report(metrics: dict, findings: list[Finding]) -> str:
    """Human-readable QA block, appended to generated script files."""
    lines = ["METRICS"]
    lines += [f"  {k:<24} {v}" for k, v in metrics.items()]
    if not findings:
        lines += ["", "CHECKS  all passed"]
        return "\n".join(lines)
    lines += ["", "CHECKS"]
    for item in sorted(findings, key=lambda f: f.level != "error"):
        lines.append(f"  [{item.level.upper():<5}] {item.code}: {item.message}")
    return "\n".join(lines)
