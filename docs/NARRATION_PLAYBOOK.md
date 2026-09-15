# The Narration Playbook

How to turn a topic into a narrated explainer that people finish — the long-form,
case-study format, written for a channel where **the voice is the only production
value**: no animation, no b-roll, no music cues.

> On the reference channel: this playbook is a reconstruction of the *structure* that
> case-study explainer channels (Think School and the format it shares with Wendover,
> Polymatter, Johnny Harris) use. It is derived from watching how those videos are
> built, not from any published formula of theirs. Copy the structure, never the
> sentences.

---

## 1. Why the format holds attention

Four mechanisms, in the order they fire:

| Mechanism | What it does | Evidence base |
|---|---|---|
| **Curiosity gap** | A specific, countable fact you cannot explain creates a felt gap. Attention is the drive to close it. | Loewenstein's information-gap account of curiosity (1994) — well-supported |
| **Open loops** | Unresolved questions stay active in working memory and pull the listener forward. | Widely used in writing craft; the classic Zeigarnik effect it is named after has *weak* replication — treat the mechanism as a craft heuristic, not a settled finding |
| **Narrative transport** | A story with named people, a year and a place is recalled and followed better than the same content as exposition. | Narrative-vs-expository recall advantage is robustly replicated |
| **Segmentation** | Attention decays over minutes. A hard structural break — "But here is the problem." — resets it. | Consistent with segmentation effects in multimedia-learning research |

Everything below is machinery for those four.

**The core asymmetry:** a boring topic with a sharp gap outperforms an exciting topic
with no gap. You are not choosing topics. You are choosing *gaps*.

---

## 2. The beat sheet

Eleven beats. Word budgets are for a 10-minute video at 140 words per minute
(≈1,400 words). `python scripts/write_script.py --worksheet --minutes 12` prints this
rescaled to any runtime.

| # | Beat | Words | Time | The job it does |
|---|---|---|---|---|
| 1 | **Cold open** | 49 | 0:00–0:21 | Open the gap. One absurd, checkable fact. |
| 2 | **Contradiction** | 70 | 0:21–0:51 | Two things both true and incompatible. Ends on the question. |
| 3 | **Promise** | 49 | 0:51–1:12 | Three things they will understand. Three loops opened. |
| 4 | **Ground zero** | 196 | 1:12–2:36 | A person, a year, a room. The abstraction gets a face. |
| 5 | **Act 1 — the move** | 182 | 2:36–3:54 | Decision → measurable result → next problem made inevitable. |
| 6 | **Act 2 — the cost** | 182 | 3:54–5:12 | What Act 1 broke. Bigger number. **Highest drop-off zone — strongest detail goes here.** |
| 7 | **Act 3 — breaking point** | 182 | 5:12–6:30 | The old way visibly fails. Ends on the question. |
| 8 | **Mechanism reveal** | 140 | 6:30–7:30 | How it *actually* works. The payoff. Slowest, simplest sentences in the script. |
| 9 | **Counter-view** | 140 | 7:30–8:30 | The best honest argument against you. Credibility is bought here. |
| 10 | **Framework** | 126 | 8:30–9:24 | The named, portable lesson. This is what gets shared. |
| 11 | **Callback close** | 84 | 9:24–10:00 | Return to the opening number. End on a live question, not a summary. |

**Non-negotiables**
- Beat 1 contains a number. No number, no gap.
- Beat 9 exists. Skipping it is what makes a video feel like marketing.
- Beat 11 reuses a word from Beat 1. That reuse is what makes a listener feel the
  video was *built*.

---

## 3. Sentence-level craft

These are the measurable ones. `validate_script` checks every item in this table.

| Rule | Target | Why |
|---|---|---|
| Sentence length | 11–15 words average, 38 max | Spoken clauses have to fit in the listener's breath, not your eye |
| Number density | ≥2 per 100 words; spoken scripts usually land 4-9 | Numbers are the difference between analysis and opinion. Spelled-out numbers ("forty minutes") count |
| Direct address | "you" every 50–60 words | One listener, not an audience |
| Pattern interrupt | one per 90 seconds | Resets a drifting listener |
| Jargon | glossed on first use, in the same sentence | "an agent — software that picks its own next step" |
| Analogy | one per mechanism, then dropped | Kitchens, traffic, hiring, electricity bills, cricket |
| Opener | never "hi", "in this video", "today we" | The first five seconds are the whole budget |

**Pattern interrupts that work:** "But here is the problem." · "Except that is not what
happened." · "And this is where it breaks." · "Now hold that number." · "So what
changed?"

**One claim per sentence.** Two claims in one sentence means the listener retains
neither. This single habit does more for clarity than everything else on this page.

---

## 4. Voice-only delivery

You have no visuals. Four substitutes:

1. **Pause as an edit.** A full stop is 0.3s. A beat change is 1.2s. The listener hears
   the chapter break you cannot show.
2. **Pitch drop for the reveal.** Drop pitch and slow ~20% for the mechanism beat.
   Speed back up for acts.
3. **Verbal b-roll.** Instead of "the system failed", say "at 2 a.m. their dashboard
   turned red and 4,000 orders sat frozen". The listener renders the image for you.
4. **Count out loud.** "Three reasons. One… two… three…" Spoken lists need audible
   numbering; a viewer cannot see your bullet points.

Record beat by beat, not in one take. The beat sheet is also your edit list.

---

## 5. Topic → script, in seven answers

Do not open a document until all seven are answered. If any is hard, the video is not
ready — that is the worksheet's job, not a formality.

1. **The number.** What countable fact makes someone stop? (Arithmetic you can derive
   beats a survey statistic you must trust.)
2. **The contradiction.** What two true things cannot both be true?
3. **The character.** Which company, team or person — with a year and a place?
4. **The three acts.** Three escalating concrete events, not three observations.
5. **The mechanism.** How does it work, in 120 words, with one everyday analogy?
6. **The dark side.** What is the strongest honest case against your conclusion?
7. **The framework.** Name the lesson in 2–4 words.

### Applied to your beats

| Your topic area | Weak framing (no gap) | Strong framing (gap) |
|---|---|---|
| Agentic AI | "What are AI agents?" | "Software that is right 95% of the time, and fails 2 out of 3 jobs. Same software." |
| AI + economy | "AI will change jobs" | "The task that got 40× cheaper, and the salary in that job that did not move" |
| AI + politics | "AI regulation explained" | "Two countries wrote the same AI law. One of them cannot enforce a single line of it." |
| AI + race/bias | "AI is biased" | "The system passed every fairness test it was given — and the tests were the problem." |

The pattern in every strong framing: **a specific quantity, and something that should
not be true of it.**

---

## 6. Fact integrity

This channel's whole value is that a claim from it can be repeated without
embarrassment. Three rules:

1. Every number spoken aloud gets a row in the **fact ledger** at the bottom of the
   script file: claim as spoken · source · CONFIRMED or UNVERIFIED.
2. An UNVERIFIED number is narrated as a claim — "according to their filing",
   "reportedly" — or cut.
3. Prefer **derivable** numbers. "95% right per step, twenty steps, 0.95²⁰ — about 36%"
   is checkable by the listener with a calculator. It can never be wrong, and it
   cannot be fact-checked in the comments.

Generated research passes emit CONFIRMED/UNVERIFIED tags and a DO NOT CLAIM list for
exactly this reason. Do not delete those columns.

---

## 7. The tooling

```bash
# blank worksheet for writing by hand — no API key needed
python scripts/write_script.py --worksheet --minutes 12

# generate: research → beat sheet → narration → QA
python scripts/write_script.py --topic "Why enterprise AI agents fail in production"

# stop at the beat sheet, edit the story, then write from your edit
python scripts/write_script.py --topic "..." --stop-after outline
python scripts/write_script.py --topic "..." --outline out/scripts/<slug>.outline.json

# QA a script you wrote yourself
python scripts/write_script.py --check my_script.txt --minutes 12
```

Generation is three passes on purpose. A single "write a 10-minute script" call
produces 1,400 words of shapeless summary — the structural decisions have to be made
and inspected *before* anything is written as prose. The beat sheet is the cheap place
to fix a bad story.

The QA pass (`backend/app/pipeline/narrative.py`) measures, it does not judge: word
count, opener strength, number density, sentence length, direct address, pattern
interrupts, unglossed jargon, and whether the close calls back to the open. `error`
means the format is broken. `warn` can be deliberate.

**Worked example:** [`docs/examples/agentic_ai_case_study_script.md`](examples/agentic_ai_case_study_script.md)
— a complete 10-minute script in this format, with its beat sheet, QA output and fact
ledger.

---

## 8. Pre-record checklist

- [ ] First sentence has a number and no greeting
- [ ] I can state the contradiction in one breath
- [ ] Three acts are three *events*, not three topics
- [ ] After the mechanism beat, a listener could explain it to a friend
- [ ] The counter-argument is one a smart opponent would actually make
- [ ] The framework has a name I said out loud
- [ ] The last 30 seconds return to the opening number
- [ ] Every number has a fact-ledger row, and every UNVERIFIED one is spoken as a claim
- [ ] `--check` reports zero errors
