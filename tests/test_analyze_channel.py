"""Tests for the transcript analyzer's parsing and measurement."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_channel import analyze, load_transcript, parse_timed  # noqa: E402

# YouTube auto-captions repeat the previous line in each cue to make the scrolling
# effect. Naive concatenation would count "the first line" three times.
ROLLING_VTT = """WEBVTT
Kind: captions
Language: en

00:00:00.000 --> 00:00:04.000
ninety five percent of the market

00:00:04.000 --> 00:00:08.000
ninety five percent of the market
was held by one company

00:00:08.000 --> 00:00:12.000
was held by one company
but here is the problem
"""

SRT = """1
00:00:01,000 --> 00:00:03,000
forty thousand units a year

2
00:00:03,000 --> 00:00:05,000
and this is where it breaks
"""


def test_rolling_duplicates_are_collapsed():
    cues = parse_timed(ROLLING_VTT)
    text = " ".join(c.text for c in cues)
    assert text.count("ninety five percent of the market") == 1
    assert text.count("was held by one company") == 1
    assert "but here is the problem" in text


def test_srt_is_parsed_and_cue_numbers_dropped():
    cues = parse_timed(SRT)
    assert [c.start for c in cues] == [1.0, 3.0]
    assert "1" not in [c.text for c in cues]
    assert cues[0].text == "forty thousand units a year"


def test_timestamps_are_seconds():
    cues = parse_timed("WEBVTT\n\n01:02:03.500 --> 01:02:06.000\nhello there\n")
    assert cues[0].start == pytest.approx(3723.5)


def test_analyze_finds_first_number_and_interrupts():
    cues = parse_timed(ROLLING_VTT)
    text = " ".join(c.text for c in cues)
    rep = analyze("sample", cues, text)
    assert rep.first_number_s == 0.0
    assert rep.interrupts_pct  # "but here is the problem" is a structural break
    assert rep.metrics["words"] > 0


def test_plain_text_transcript_has_no_cues(tmp_path):
    p = tmp_path / "script.txt"
    p.write_text("Ninety-five percent.  That is the number.\n")
    cues, text = load_transcript(p)
    assert cues == []
    assert text == "Ninety-five percent. That is the number."
