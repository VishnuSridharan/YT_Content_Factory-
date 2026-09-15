"""Measure the narration format of a real channel, video by video.

Feeds transcripts through the same metrics as scripts/write_script.py --check, then
reports the *shape* of the format: where the first number lands, where the pattern
interrupts fall as a percentage of runtime, how pacing changes across the video, and
whether the close calls back to the open.

This is how you replace an assumed beat sheet with a measured one.

Two input modes:

    # A: let yt-dlp pull the channel's most-viewed videos and their auto-captions
    pip install yt-dlp
    python scripts/analyze_channel.py --channel https://www.youtube.com/@ThinkSchool --top 10

    # B: transcripts you already have (.vtt, .srt or .txt in a folder)
    python scripts/analyze_channel.py --transcripts ./transcripts

Output: out/analysis/<name>.md plus a per-video JSON dump.

Note on mode A: YouTube must be reachable. Sandboxed/CI environments usually block it —
run this one locally.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.pipeline import narrative  # noqa: E402

OUT_DIR = ROOT / "out" / "analysis"
DECILES = 10


# ---------------------------------------------------------------------------
# Transcript parsing
# ---------------------------------------------------------------------------

_TIMESTAMP = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[.,](\d{3})"
)
_TAG = re.compile(r"<[^>]+>")


@dataclass
class Cue:
    start: float
    text: str


def parse_timed(text: str) -> list[Cue]:
    """Parse VTT or SRT into cues, collapsing YouTube's rolling duplicate lines.

    Auto-generated captions repeat the previous line in each cue to create the
    scrolling effect, so naive concatenation doubles the word count.
    """
    cues: list[Cue] = []
    start: float | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, start
        if start is not None and buffer:
            line = " ".join(buffer).strip()
            if line:
                cues.append(Cue(start, line))
        buffer = []

    for raw in text.splitlines():
        line = _TAG.sub("", raw).strip()
        m = _TIMESTAMP.search(line)
        if m:
            flush()
            h, mm, s, ms = (int(m.group(i)) for i in range(1, 5))
            start = h * 3600 + mm * 60 + s + ms / 1000
            continue
        if not line or line.upper().startswith(("WEBVTT", "KIND:", "LANGUAGE:")):
            continue
        if line.isdigit():  # SRT cue number
            continue
        buffer.append(line)
    flush()

    # Drop text already carried by the previous cue (the rolling-window duplicate).
    cleaned: list[Cue] = []
    for cue in cues:
        if cleaned:
            prev = cleaned[-1].text
            if cue.text == prev:
                continue
            if cue.text.startswith(prev):
                cue = Cue(cue.start, cue.text[len(prev) :].strip())
            elif prev.endswith(cue.text):
                continue
        if cue.text:
            cleaned.append(cue)
    return cleaned


def load_transcript(path: Path) -> tuple[list[Cue], str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in (".vtt", ".srt"):
        cues = parse_timed(raw)
        return cues, " ".join(c.text for c in cues)
    return [], re.sub(r"\s+", " ", raw).strip()


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------


@dataclass
class VideoReport:
    name: str
    duration_s: float
    metrics: dict = field(default_factory=dict)
    first_number_s: float | None = None
    hook_text: str = ""
    interrupts_pct: list[int] = field(default_factory=list)
    decile_numbers: list[float] = field(default_factory=list)
    decile_sentence_len: list[float] = field(default_factory=list)
    callback: bool = False

    def as_dict(self) -> dict:
        d = dict(self.__dict__)
        d["duration_min"] = round(self.duration_s / 60, 1)
        return d


def analyze(name: str, cues: list[Cue], text: str) -> VideoReport:
    metrics = narrative.script_metrics(text)
    words = narrative._words(text)
    duration = cues[-1].start if cues else metrics["words"] / narrative.WORDS_PER_MINUTE * 60
    rep = VideoReport(name=name, duration_s=duration, metrics=metrics)

    # When does the first hard number arrive? The hook's whole job.
    if cues:
        for cue in cues:
            if any(narrative._is_numeric(w) for w in narrative._words(cue.text)):
                rep.first_number_s = round(cue.start, 1)
                break
        rep.hook_text = " ".join(c.text for c in cues if c.start <= 30)[:400]
    else:
        for i, w in enumerate(words):
            if narrative._is_numeric(w):
                rep.first_number_s = round(i / narrative.WORDS_PER_MINUTE * 60, 1)
                break
        rep.hook_text = " ".join(words[:70])

    # Where do the structural breaks fall, as a share of runtime? This is the
    # empirical beat map: cluster these across videos and the format falls out.
    if cues and duration:
        for cue in cues:
            low = cue.text.lower()
            if any(marker in low for marker in narrative.INTERRUPT_MARKERS):
                rep.interrupts_pct.append(int(cue.start / duration * 100))

    # Pacing shape across the video.
    chunk = max(1, len(words) // DECILES)
    for i in range(DECILES):
        seg = words[i * chunk : (i + 1) * chunk]
        if not seg:
            continue
        seg_text = " ".join(seg)
        m = narrative.script_metrics(seg_text)
        rep.decile_numbers.append(m["numbers_per_100_words"])
        rep.decile_sentence_len.append(m["avg_sentence_words"])

    open_n = min(45, max(8, len(words) // 3))
    close_n = min(70, max(10, len(words) // 3))
    rep.callback = bool(
        narrative._content_words(" ".join(words[:open_n]))
        & narrative._content_words(" ".join(words[-close_n:]))
    )
    return rep


# ---------------------------------------------------------------------------
# Fetching (mode A)
# ---------------------------------------------------------------------------


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600)


def fetch_channel(channel: str, top: int, workdir: Path) -> list[Path]:
    """Pull the channel's most-viewed videos' auto-captions with yt-dlp."""
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"listing {channel} …")
    listing = _run(
        [
            "yt-dlp", "--flat-playlist", "-J", "--playlist-end", "200",
            f"{channel.rstrip('/')}/videos",
        ]
    )
    if listing.returncode != 0:
        raise SystemExit(
            "yt-dlp could not list the channel.\n"
            f"{listing.stderr.strip()[:500]}\n\n"
            "If this says 'Tunnel connection failed' or 403, YouTube is blocked by this "
            "machine's network policy — run this script locally instead."
        )
    entries = json.loads(listing.stdout).get("entries", [])
    ranked = sorted(entries, key=lambda e: e.get("view_count") or 0, reverse=True)[:top]
    print(f"{len(entries)} videos found; taking the {len(ranked)} most-viewed")

    paths: list[Path] = []
    for i, entry in enumerate(ranked, 1):
        vid = entry.get("id")
        title = re.sub(r"[^A-Za-z0-9]+", "-", entry.get("title") or vid).strip("-")[:60]
        views = entry.get("view_count") or 0
        print(f"  [{i}/{len(ranked)}] {views:>12,} views  {title}")
        out = workdir / f"{i:02d}_{title}"
        res = _run(
            [
                "yt-dlp", "--skip-download",
                "--write-auto-sub", "--write-sub", "--sub-lang", "en.*",
                "--sub-format", "vtt", "--convert-subs", "vtt",
                "-o", str(out), f"https://www.youtube.com/watch?v={vid}",
            ]
        )
        found = sorted(workdir.glob(f"{i:02d}_{title}*.vtt"))
        if found:
            paths.append(found[0])
        else:
            why = res.stderr.strip().splitlines()[-1][:120] if res.stderr else "—"
            print(f"      no captions available ({why})")
    return paths


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2


def build_report(reports: list[VideoReport], label: str) -> str:
    if not reports:
        return "# No transcripts analysed\n"
    lines = [
        f"# Narration format analysis — {label}",
        "",
        f"{len(reports)} videos measured with `backend/app/pipeline/narrative.py`.",
        "",
        "## Per video",
        "",
        "| Video | Min | Words | WPM | Avg sent. | Num/100w | You/100w | 1st number | Callback |",
        "|---|--:|--:|--:|--:|--:|--:|--:|:--:|",
    ]
    for r in reports:
        m = r.metrics
        wpm = round(m["words"] / (r.duration_s / 60)) if r.duration_s else 0
        first = f"{r.first_number_s:.0f}s" if r.first_number_s is not None else "—"
        lines.append(
            f"| {r.name[:42]} | {r.duration_s / 60:.1f} | {m['words']} | {wpm} | "
            f"{m['avg_sentence_words']} | {m['numbers_per_100_words']} | "
            f"{m['you_per_100_words']} | {first} | {'yes' if r.callback else 'no'} |"
        )

    wpms = [r.metrics["words"] / (r.duration_s / 60) for r in reports if r.duration_s]
    firsts = [r.first_number_s for r in reports if r.first_number_s is not None]
    med_sentence = _median([r.metrics["avg_sentence_words"] for r in reports])
    med_numbers = _median([r.metrics["numbers_per_100_words"] for r in reports])
    med_you = _median([r.metrics["you_per_100_words"] for r in reports])
    lines += [
        "",
        "## Medians",
        "",
        "| Measure | Median | Playbook assumption |",
        "|---|--:|--:|",
        f"| Runtime (min) | {_median([r.duration_s / 60 for r in reports]):.1f} | 10 |",
        f"| Words per minute | {_median(wpms):.0f} | {narrative.WORDS_PER_MINUTE} |",
        f"| Avg sentence (words) | {med_sentence:.1f} | 11-15 |",
        f"| Numbers per 100 words | {med_numbers:.1f} | ≥2 |",
        f"| 'you' per 100 words | {med_you:.1f} | ≥0.5 |",
        f"| First number at | {_median(firsts):.0f}s | <20s |",
        f"| Callback close | {sum(r.callback for r in reports)}/{len(reports)} | always |",
        "",
        "## Structural breaks (pattern interrupts, as % of runtime)",
        "",
        "Cluster these across videos and the real beat map falls out: a column that",
        "appears in most videos is a beat boundary the channel actually uses.",
        "",
        "| Video | Break positions (%) |",
        "|---|---|",
    ]
    for r in reports:
        pos = ", ".join(str(p) for p in r.interrupts_pct) or "—"
        lines.append(f"| {r.name[:42]} | {pos} |")

    buckets = [0] * DECILES
    for r in reports:
        for p in r.interrupts_pct:
            buckets[min(DECILES - 1, p // DECILES)] += 1
    lines += [
        "",
        "Breaks per tenth of the video, summed over all videos:",
        "",
        "```",
        "  " + "  ".join(f"{i * 10:>3}%" for i in range(DECILES)),
        "  " + "  ".join(f"{b:>4}" for b in buckets),
        "```",
        "",
        "## Pacing shape (median across videos, by tenth)",
        "",
        "```",
    ]
    for name, key in (("numbers/100w", "decile_numbers"), ("avg sentence", "decile_sentence_len")):
        per_decile = []
        for i in range(DECILES):
            vals = [getattr(r, key)[i] for r in reports if len(getattr(r, key)) > i]
            per_decile.append(_median(vals))
        lines.append(f"{name:>14}  " + "  ".join(f"{v:>5.1f}" for v in per_decile))
    lines += [
        "```",
        "",
        "A dip in sentence length late in the video is the mechanism/reveal beat — the",
        "narrator slowing down. A spike in number density early is the hook.",
        "",
        "## Hooks, verbatim (first 30 seconds)",
        "",
    ]
    for r in reports:
        lines += [f"**{r.name[:60]}**", "", f"> {r.hook_text}", ""]
    lines += [
        "## How to use this",
        "",
        "1. Compare the medians column against the playbook assumptions and update",
        "   `BEAT_SHEET` shares in `backend/app/pipeline/narrative.py` where they differ.",
        "2. Read the hooks back to back. The repeated *move* — not the wording — is the",
        "   thing to copy.",
        "3. Auto-captions have no punctuation model worth trusting: sentence-length numbers",
        "   are indicative, not exact. Word counts, number density and timings are reliable.",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--channel", help="channel URL; fetches most-viewed videos via yt-dlp")
    ap.add_argument("--top", type=int, default=10, help="how many videos to analyse (default 10)")
    ap.add_argument("--transcripts", help="folder of .vtt/.srt/.txt files to analyse instead")
    ap.add_argument("--label", default="", help="name for the report")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.transcripts:
        folder = Path(args.transcripts)
        paths = sorted(
            p for p in folder.iterdir() if p.suffix.lower() in (".vtt", ".srt", ".txt")
        )
        if not paths:
            print(f"no .vtt/.srt/.txt files in {folder}", file=sys.stderr)
            return 1
        label = args.label or folder.name
    elif args.channel:
        try:
            paths = fetch_channel(args.channel, args.top, OUT_DIR / "captions")
        except FileNotFoundError:
            print("yt-dlp not installed. Run: pip install yt-dlp", file=sys.stderr)
            return 1
        if not paths:
            print("no captions could be downloaded", file=sys.stderr)
            return 1
        label = args.label or args.channel
    else:
        ap.error("pass --channel or --transcripts")

    reports = []
    for p in paths:
        cues, text = load_transcript(p)
        if len(text.split()) < 100:
            print(f"skipping {p.name}: too short to measure")
            continue
        reports.append(analyze(p.stem, cues, text))

    slug = re.sub(r"[^A-Za-z0-9]+", "-", label).strip("-").lower()[:50] or "analysis"
    md = OUT_DIR / f"{slug}.md"
    md.write_text(build_report(reports, label), encoding="utf-8")
    (OUT_DIR / f"{slug}.json").write_text(
        json.dumps([r.as_dict() for r in reports], indent=2), encoding="utf-8"
    )
    print(f"\n{len(reports)} videos analysed\nwritten: {md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
