"""Unit tests for the long-form narration beat sheet and script validator."""

from __future__ import annotations

import pytest
from app.pipeline import narrative
from app.pipeline.narrative import BEAT_SHEET, plan_beats, script_metrics, validate_script


def _codes(findings):
    return {f.code for f in findings}


def _minutes(text: str) -> float:
    """Exact target runtime for a sample, so the length check never masks the one under test."""
    return len(text.split()) / narrative.WORDS_PER_MINUTE


def test_beat_shares_sum_to_one():
    assert sum(b.share for b in BEAT_SHEET) == pytest.approx(1.0, abs=1e-9)


def test_beat_keys_unique():
    keys = [b.key for b in BEAT_SHEET]
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("minutes", [6, 10, 14.5])
def test_plan_budget_matches_runtime(minutes):
    plans = plan_beats(minutes)
    total = sum(p.words for p in plans)
    expected = minutes * narrative.WORDS_PER_MINUTE
    # rounding per beat, so allow a few words of drift
    assert abs(total - expected) <= len(plans)
    assert plans[0].start_s == 0
    assert plans[-1].end_s == pytest.approx(minutes * 60, abs=5)


def test_plans_are_contiguous():
    plans = plan_beats(10)
    for a, b in zip(plans, plans[1:], strict=False):
        assert b.start_s == a.end_s


@pytest.mark.parametrize(
    "token,expected",
    [
        ("2024", True),
        ("40%", True),
        ("ninety-five", True),
        ("forty", True),
        ("nearly-perfect", False),
        ("model", False),
    ],
)
def test_numeric_token_detection(token, expected):
    assert narrative._is_numeric(token) is expected


def test_spelled_out_numbers_count_as_specifics():
    m = script_metrics("Ninety-five percent of forty tickets came back in twelve minutes.")
    assert m["numbers_per_100_words"] > 20


def test_weak_opener_and_missing_hook_number_are_errors():
    text = "Hey guys, welcome back to the channel. Today we are going to talk about agents. " * 6
    _, findings = validate_script(text, target_minutes=_minutes(text))
    assert "weak_opener" in _codes(findings)
    assert "no_hook_number" in _codes(findings)


def test_clean_script_passes_every_check():
    _, findings = validate_script(GOOD, target_minutes=_minutes(GOOD))
    assert [f for f in findings if f.level == "error"] == []
    assert _codes(findings) == set()


def test_missing_callback_is_flagged():
    # opens on the thirty-six percent image and never returns to it
    _, findings = validate_script(NO_CALLBACK, target_minutes=_minutes(NO_CALLBACK))
    assert "no_callback" in _codes(findings)


def test_unglossed_jargon_is_flagged():
    text = (
        "Ninety-five percent of runs fail. The agent calls an API and the latency kills it. "
        "You lose the thread. This is the shape of the problem. But here is the problem. "
        "It never ends. That is the ninety-five percent again."
    )
    _, findings = validate_script(text, target_minutes=_minutes(text))
    assert "unglossed_jargon" in _codes(findings)


def test_run_on_sentence_is_flagged():
    long_sentence = " ".join(["word"] * 45) + "."
    text = "Ninety-five percent. " + long_sentence
    _, findings = validate_script(text, target_minutes=_minutes(text))
    assert "run_on" in _codes(findings)


def test_empty_script_errors():
    _, findings = validate_script("   ", target_minutes=10)
    assert _codes(findings) == {"empty"}


# A short script that satisfies every rule: numeric hook, short sentences, direct
# address, glossed jargon, pattern interrupts, and a close that calls back.
GOOD = """Ninety-five percent. That is how often the agent gets one step right.
Now give it twenty steps. The answer is thirty-six percent.
An agent — software that picks its own next step — never notices it is wrong.
You would notice. You would scroll up and re-read the number.
But here is the problem. It does not.
So it continues, confidently, for eight more steps.
And this is where it breaks. Every fix you add is another step.
Twenty steps at ninety-five percent is thirty-six percent.
Shorten the chain. Check the seams. Keep the cost of failure low.
That is what thirty-six percent was telling you all along."""


# Opens on the same hook as GOOD, then drifts away and closes on something unrelated —
# the shape of a script whose ending was written on a different day.
NO_CALLBACK = """Ninety-five percent. That is how often the agent gets one step right.
Now give it twenty steps. The answer is thirty-six percent.
An agent — software that picks its own next step — never notices it is wrong.
But here is the problem. The rollout ran through spring.
Two departments argued about budget ownership for eleven weeks.
Nobody wrote the decisions down anywhere you could find them later.
And this is where it breaks. A third vendor was invited in March.
Procurement asked for four references and received one.
Legal reviewed the contract twice and flagged nine clauses.
The pilot slipped to July, then to September, then off the roadmap entirely.
Contracts like that take about six months to unwind.
You should expect roughly that timeline on your own renewal."""
