"""Turn a topic into a full long-form narration script, in the case-study format.

Three LLM passes — research, beat sheet, script — then a mechanical QA pass.
The beat sheet is written to disk between passes, so you can edit it (the cheap
place to fix a bad story) and re-run only the final pass.

Usage:
    # blank fill-in worksheet, no LLM, no API key needed
    python scripts/write_script.py --worksheet --minutes 10

    # full generation
    python scripts/write_script.py --topic "Why enterprise AI agents fail in production"

    # stop after the beat sheet, edit it, then write the script from it
    python scripts/write_script.py --topic "..." --stop-after outline
    python scripts/write_script.py --topic "..." --outline out/scripts/<slug>.outline.json

    # QA a script you wrote yourself
    python scripts/write_script.py --check my_script.txt --minutes 12

Output lands in out/scripts/<slug>.md — beat sheet, narration, QA report, fact ledger.
Exit codes: 0 = script written, 1 = generation failed, 2 = QA found format errors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.pipeline import narrative  # noqa: E402
from app.pipeline import prompts_narrative as P  # noqa: E402

OUT_DIR = ROOT / "out" / "scripts"
DEFAULT_AUDIENCE = (
    "curious non-specialists who follow technology, business and politics; "
    "smart, impatient, allergic to being lectured; not engineers"
)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "script"


def beat_spec(minutes: float) -> str:
    """The beat sheet rendered for a prompt."""
    return "\n".join(
        f"- {p.beat.key} | {p.beat.name} | ~{p.words} words ({p.timecode}) | "
        f"{p.beat.purpose} {p.beat.guidance}"
        for p in narrative.plan_beats(minutes)
    )


def worksheet(minutes: float) -> str:
    """A blank beat sheet to fill in by hand — the format without the machine."""
    lines = [
        f"# Script worksheet — {minutes:g} minute narration",
        "",
        "Fill every line before you write a single sentence of prose. If a line is hard,",
        "the video is not ready — that is the point of the worksheet.",
        "",
        "TOPIC:",
        "CORE QUESTION (one sentence the video answers):",
        "ONE-LINE SUMMARY (the whole video in one sentence):",
        "",
    ]
    for p in narrative.plan_beats(minutes):
        lines += [
            f"## {p.beat.name}  —  ~{p.words} words  ({p.timecode})",
            f"_{p.beat.purpose}_",
            f"_{p.beat.guidance}_",
            "",
            "> ",
            "",
        ]
    lines += [
        "## Fact ledger",
        "",
        "| # | Claim as spoken | Source | Status |",
        "|---|-----------------|--------|--------|",
        "| 1 |  |  | CONFIRMED / UNVERIFIED |",
        "",
        "Rule: every number spoken aloud has a row here. An UNVERIFIED row must be",
        "narrated as a claim (\"according to…\"), never as a fact.",
    ]
    return "\n".join(lines)


def generate(topic: str, minutes: float, audience: str, stop_after: str, outline_path: Path | None):
    from app.core.logging import logger, setup_logging
    from app.pipeline.llm import get_llm

    setup_logging()
    llm = get_llm()
    slug = slugify(topic)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("[1/3] research: {}", topic)
    research = llm.chat(
        P.RESEARCH_PROMPT.format(topic=topic, minutes=minutes, audience=audience),
        system=P.RESEARCH_SYSTEM,
        temperature=0.4,
    )
    (OUT_DIR / f"{slug}.research.md").write_text(research, encoding="utf-8")
    if stop_after == "research":
        return None

    if outline_path:
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        logger.info("[2/3] outline: reusing {}", outline_path)
    else:
        logger.info("[2/3] beat sheet")
        outline = llm.chat_json(
            P.OUTLINE_PROMPT.format(
                topic=topic,
                minutes=minutes,
                audience=audience,
                research=research,
                beat_spec=beat_spec(minutes),
            ),
            system=P.OUTLINE_SYSTEM,
        )
        if isinstance(outline, list):
            outline = {"title": topic, "one_line": "", "beats": outline}
        (OUT_DIR / f"{slug}.outline.json").write_text(
            json.dumps(outline, indent=2), encoding="utf-8"
        )
    if stop_after == "outline":
        return None

    plans = {p.beat.key: p for p in narrative.plan_beats(minutes)}
    written = {b.get("key"): b.get("content", "") for b in outline.get("beats", [])}
    placeholder = "(decide this yourself, following the beat purpose)"
    outline_block = "\n".join(
        f"[{p.beat.key}] {p.beat.name} — ~{p.words} words\n"
        f"    {written.get(p.beat.key) or placeholder}"
        for p in plans.values()
    )

    logger.info("[3/3] script")
    script = llm.chat(
        P.SCRIPT_PROMPT.format(
            topic=topic,
            minutes=minutes,
            audience=audience,
            target_words=int(minutes * narrative.WORDS_PER_MINUTE),
            outline_block=outline_block,
            research=research,
        ),
        system=P.SCRIPT_SYSTEM,
        temperature=0.75,
    )
    from app.pipeline.nodes.text_nodes import _clean_text

    return slug, outline, _clean_text(script), research


def write_output(slug: str, topic: str, outline: dict, script: str, minutes: float) -> Path:
    metrics, findings = narrative.validate_script(script, minutes)
    path = OUT_DIR / f"{slug}.md"
    body = [
        f"# {outline.get('title') or topic}",
        "",
        f"_{date.today().isoformat()} · target {minutes:g} min · "
        f"{metrics['words']} words ≈ {metrics['runtime_minutes']} min read aloud_",
        "",
        f"**One line:** {outline.get('one_line', '')}",
        "",
        "## Beat sheet",
        "",
    ]
    for b in outline.get("beats", []):
        name = narrative.BEATS_BY_KEY.get(b.get("key"), None)
        body.append(f"- **{name.name if name else b.get('key')}** — {b.get('content', '')}")
    body += ["", "## Narration", "", script, ""]
    body += ["## QA", "", "```", narrative.format_report(metrics, findings), "```", ""]
    body += [
        "## Fact ledger",
        "",
        "| # | Claim as spoken | Source | Status |",
        "|---|-----------------|--------|--------|",
        "| 1 |  |  | CONFIRMED / UNVERIFIED |",
        "",
        "Every number in the narration needs a row. Verify before you record.",
    ]
    path.write_text("\n".join(body), encoding="utf-8")
    print(narrative.format_report(metrics, findings))
    return path


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--topic", help="what the video is about")
    ap.add_argument("--minutes", type=float, default=10.0, help="target runtime (default 10)")
    ap.add_argument("--audience", default=DEFAULT_AUDIENCE)
    ap.add_argument("--worksheet", action="store_true", help="print a blank beat sheet; no LLM")
    ap.add_argument("--check", metavar="FILE", help="QA an existing script file; no LLM")
    ap.add_argument("--stop-after", choices=["research", "outline", "script"], default="script")
    ap.add_argument("--outline", metavar="FILE", help="reuse an edited beat-sheet JSON")
    args = ap.parse_args()

    if args.worksheet:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        text = worksheet(args.minutes)
        path = OUT_DIR / "worksheet.md"
        path.write_text(text, encoding="utf-8")
        print(text)
        print(f"\nwritten: {path}")
        return 0

    if args.check:
        text = Path(args.check).read_text(encoding="utf-8")
        metrics, findings = narrative.validate_script(text, args.minutes)
        print(narrative.format_report(metrics, findings))
        return 2 if any(f.level == "error" for f in findings) else 0

    if not args.topic:
        ap.error("--topic is required (or use --worksheet / --check)")

    try:
        result = generate(
            args.topic,
            args.minutes,
            args.audience,
            args.stop_after,
            Path(args.outline) if args.outline else None,
        )
    except Exception as e:  # noqa: BLE001
        print(f"generation failed: {e}", file=sys.stderr)
        return 1
    if result is None:
        print(f"stopped after {args.stop_after}; intermediate files in {OUT_DIR}")
        return 0

    slug, outline, script, _research = result
    path = write_output(slug, args.topic, outline, script, args.minutes)
    print(f"\nwritten: {path}")
    _, findings = narrative.validate_script(script, args.minutes)
    return 2 if any(f.level == "error" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
