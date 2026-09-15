# The 36% Problem: why "95% accurate" AI agents fail two times out of three

_Worked example of the format in [`docs/NARRATION_PLAYBOOK.md`](../NARRATION_PLAYBOOK.md).
Target 10 minutes · 140 wpm · ~1,400 words._

**One line:** Agent reliability multiplies instead of averaging, so the gap between a
demo and production is arithmetic, not engineering skill.

---

## Beat sheet

| Beat | Content |
|---|---|
| Cold open | 95% per step, 20 steps, 36% end-to-end. |
| Contradiction | Models measurably improved; deployments measurably did not. |
| Promise | Why it fails, why it is not a model problem, what actually fixes it. |
| Ground zero | A composite support-automation team, 2024 — 40 minutes per ticket. |
| Act 1 | The 12-step demo works. Leadership funds it. |
| Act 2 | Live tickets: humans re-check everything, and checking costs more than doing. |
| Act 3 | They fix it by adding steps. The chain gets longer and reliability falls further. |
| Mechanism | Reliability multiplies. Humans self-correct; the chain does not notice it is wrong. |
| Counter-view | At 99% per step it is 82% — and for cheap-to-retry work agents already win. |
| Framework | **The reliability tax**: shorten the chain, verify at the seams, make failure cheap. |
| Close | Back to 36%, and the real question: which of your steps can be wrong safely? |

---

## Narration

Ninety-five percent. That is how often a well-built AI agent gets a single step right.
Now give that agent twenty steps to finish a real job. The answer is not ninety-five
percent. It is thirty-six. The same software that looked flawless in the demo will fail
you two times out of three.

And here is what makes that strange. The models genuinely got better. On the public
tests, on coding, on reasoning, the numbers moved up year after year. The engineers
building on top of them are not amateurs. So both of these are true at once: the
technology improved, and the projects kept dying. Something sits between a model that
works and a system that works. Almost nobody talks about it, because it is not a
technology problem at all.

By the end of this, you will understand three things. One, why nearly-perfect software
produces mostly-broken results. Two, why buying a better model does not fix it. And
three, the three design rules that separate the agent projects that ship from the ones
quietly deleted after six months.

Picture a support team in 2024. I am describing a composite here — this is the shape of
a hundred real teams, not one company I can name. Forty people, answering customer
tickets. Each ticket takes about forty minutes. Read it, find the customer's account,
check the order, check the refund policy, decide, write the reply, update the record,
close the ticket. Seven steps, forty minutes, nine hundred times a week. Their head of
support does the multiplication one evening and sees six hundred hours a week going
into work where five of those seven steps are pure lookup. A machine should do lookups.
So she asks two engineers for a prototype.

They build it in three weeks, and it is genuinely impressive. They wire a language model
to their internal tools, so it can look things up and take actions on its own. That is
all an agent is, by the way — a model that decides its own next step and is allowed to
use tools, instead of just producing text. Their agent runs twelve steps for a ticket.
It reads, it looks up, it checks, it drafts, it updates. In the demo it takes a real
ticket and closes it in ninety seconds. Forty minutes to ninety seconds. Leadership
funds it the same week. And that demo was not faked — that part is important. It worked.

Then it meets live tickets. Not broken, exactly. Just wrong often enough. It refunds an
order that was already refunded. It quotes a policy that changed in March. It closes a
ticket where the customer asked two questions and it answered one. Roughly four tickets
in ten come back needing a human. But here is the part that actually kills the project.
Because any ticket could be the wrong one, every ticket has to be checked. A human now
reads the agent's twelve steps, decides whether to trust it, and half the time redoes
the work. Verification takes eleven minutes. The original ticket took forty. They
budgeted for a ninety-five percent saving and got a thirty percent saving, on work the
team now no longer trusts.

So they do the obvious thing. They fix it. They add a step that double-checks the refund
status. A step that re-reads the latest policy. A step that confirms every question got
an answer. Sensible fixes, each one aimed at a real failure. Their twelve-step agent
becomes a twenty-step agent. And the pass rate goes down. Not up. Down. The team is now
in the strangest position in software: every individual fix is correct, and the system
keeps getting worse. Why?

Now hold that number, twenty, in your head. Because reliability does not average. It
multiplies. Ninety-five percent right, twenty
times in a row, is zero point nine five to the power of twenty. That is thirty-six
percent. Take out your phone and check it — this is arithmetic, not an opinion. Five
steps is seventy-seven percent. Twelve steps is fifty-four percent. Twenty steps is
thirty-six. Every step you add to make it safer is another number you multiply by.

Now, you run twenty-step processes every day and you do not fail two times out of three.
Why not? Because you notice. You feel the refund looks wrong and you scroll up. You
re-read the policy because something nags. A human chain is not twenty independent
steps — it is twenty steps with a checker running alongside them. The agent has no such
checker. It cannot tell the difference between a step that went right and a step that
went wrong. It just takes its own last output as true and continues, confidently, for
eight more steps. That is the whole gap. Not intelligence. Error detection.

But here is the strongest argument against everything I have just said. Models are
getting better, and that changes the multiplication. At ninety-nine percent per step,
twenty steps gives you eighty-two percent, not thirty-six. That is a real jump, and it
is coming. Two honest caveats, though. Eighty-two percent still means one job in five is
wrong, which in a refunds pipeline is not a rounding error. And as models get more
capable, teams give them longer chains — at ninety-nine percent, fifty steps is back
down to sixty-one percent. The gains get spent. There is also a case where none of this
matters: when failure is cheap and retrying is free. Drafting code, writing a first
version, searching a codebase — you see the mistake instantly and run it again. That is
exactly where agents already earn their keep today. The trouble starts when a step
touches money, a customer, or a record you cannot un-write.

So here is the framework. Call it the reliability tax. Every step in a chain charges
you, and the bill compounds. Three rules for paying less of it.

One: shorten the chain. Not by cutting checks, but by collapsing work. Five steps at
ninety-five percent beat twenty steps at ninety-five percent by forty-one points. The
fastest quality improvement available to most teams is deletion.

Two: verify at the seams. And this is where most teams reach for the wrong tool. They add another model to review the first one. But a checker that
guesses is just a twenty-first step you now also multiply by. Put a cheap, deterministic
check between steps instead — a database lookup, a rule, a hard constraint. Boring code
that fails loudly is worth more here than a smarter model, because it restores the one
thing the chain is missing: something that notices.

Three: make failure cheap. Reversible actions run free. Irreversible ones — money out,
message sent, record deleted — get a human on the seam. Not a human checking everything.
A human standing at the two steps that cannot be undone.

That support team, by the way, ended up with a four-step agent that drafts and looks up,
and a human who presses send. Ticket time went from forty minutes to fourteen. Four steps
at ninety-five percent is seventy-seven percent, and the three ways it can fail are all
caught before anything leaves the building. Less impressive than the demo. Still in
production two years later. The demo version is in a folder somewhere, at thirty-six
percent, technically more advanced.

So thirty-six percent was never a statement about how smart the software is. It was a
statement about how long you made the chain. Which turns the real question around, and
it is the one worth sitting with before your next project: not "how accurate is the
model", but "which of my steps are allowed to be wrong?"

---

## QA

```
METRICS
  words                    1272
  sentences                123
  runtime_minutes          9.1
  avg_sentence_words       10.3
  longest_sentence_words   34
  numbers_per_100_words    9.0
  you_per_100_words        1.5
  pattern_interrupts       6

CHECKS  all passed
```

Reproduce with:
`python scripts/write_script.py --check docs/examples/agentic_ai_case_study_script.txt --minutes 10`

(The narration is kept as a plain `.txt` next to this file — that is the recording copy.)

---

## Fact ledger

| # | Claim as spoken | Source | Status |
|---|---|---|---|
| 1 | 0.95²⁰ = 36% | arithmetic — derivable by the listener | CONFIRMED |
| 2 | 0.95⁵ = 77%, 0.95¹² = 54% | arithmetic | CONFIRMED |
| 3 | 0.99²⁰ = 82%, 0.99⁵⁰ = 61% | arithmetic | CONFIRMED |
| 4 | "models improved year after year on public tests" | stated qualitatively on purpose; cite specific benchmarks with dates if you name numbers | UNVERIFIED — spoken as a general claim |
| 5 | The support team, all its numbers (40 min, 12 steps, 4 in 10, 11 min, 14 min) | **composite illustration, labelled as such in the narration** | NOT A SOURCED CLAIM |

Note how claim 5 is handled: the script says *"I am describing a composite here — this
is the shape of a hundred real teams, not one company I can name."* If you have a real,
sourced case, use it and delete that sentence. What you must never do is narrate a
composite as if it were one real company — the entire credibility of a fact-driven
channel rests on that line.

The spine of this script is claims 1–3, which are arithmetic. Nobody can fact-check you
into a correction on multiplication. Build hooks out of derivable numbers whenever the
topic allows it.
