# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I used Claude Code in agent mode for Challenge 1. I asked it to add a third algorithm that goes beyond the basic requirements: a "next available slot" finder. Then it had to use that finder to suggest a fix for each time clash, both in the command-line demo and in the Streamlit app. In the same request I also asked it to fix a bug I'd found in the app (the "Mark done" message showed a wall of junk text under it).

**What did the agent do?**

Files it changed:

- `pawpal_system.py`: added `Scheduler.find_next_slot()`, which walks the day's tasks in time order and returns the first gap that's long enough. It also added `Scheduler.suggest_move()`, which picks which task in a clash should move, and `Scheduler.find_conflicting_pairs()`, so the app gets the actual clashing tasks and not just warning text. It pulled the overlap check into a small `_overlaps()` helper, so conflict detection and the slot finder use the same rule.
- `app.py`: each clash warning now says the next free time and has a **Move ... to HH:MM** button. It also fixed the "Mark done" bug (more on that below).
- `main.py`: added a "Next free slot" section, and a suggestion line under each conflict warning.
- `tests/test_pawpal.py`: five new tests covering a normal gap, overlapping busy times, ignoring done tasks and other days, a completely full day, and the move suggestion.
- `tests/test_app.py` (new): end-to-end tests that drive the real app, including a regression test for the "Mark done" bug.
- `diagrams/uml.mmd`, `diagrams/uml_final.mmd`, and `README.md`: added the new methods.

Commands it ran to check its work: `python -m pytest` after each change, `python main.py` to look at the demo output, Streamlit's `AppTest` runner to click through the app without a browser, and a Mermaid parser to make sure the diagram still renders.

**What did you have to verify or fix manually?**

- **I found the "Mark done" bug myself, in the browser.** The agent's earlier headless checks only looked at whether the success message appeared, not at what else showed up on the page. The cause was a one-line `st.error(...) if ... else st.success(...)`. Streamlit's "magic" feature prints any bare expression, so it also dumped the return value's help text. The fix was a normal `if`/`else`. More importantly, there's now a test that checks for stray output, and I confirmed the test fails when the old line is put back.
- **The first demo didn't actually prove the feature.** The "priority order" table came out identical to the time-order table, because every high-priority task in the sample data was in the morning. And the slot finder answered 06:00, because nothing happens that early. We added a high-priority evening dinner and searched from 07:30, so the output now shows priority beating time and the slot finder skipping busy stretches.
- **A small file mistake.** `.gitignore` had no newline at the end, so adding `data.json` glued it onto the last line (`.DS_Storedata.json`). That would have stopped both entries from working. It was caught and fixed before committing, and checked with `git check-ignore`.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

**The task:** write `Task.next_occurrence()`, the logic that creates the next copy of a daily or weekly task when it's marked done. I gave both models the exact same prompt: my `Task` dataclass, the rules (daily means +1 day, weekly means +7 days, once means `None`, and the new copy isn't done), and "handle any edge cases you think matter." I didn't mention the tricky case on purpose, to see who'd catch it: a task that gets finished late.

Then I ran both answers (and my version) on the same cases:

| Case | Haiku | Sonnet | Mine |
|------|-------|--------|------|
| Daily task finished on time | tomorrow ✅ | tomorrow ✅ | tomorrow ✅ |
| Daily task due 3 days ago, finished today | 2 days ago ❌ | 2 days ago ❌ | tomorrow ✅ |
| Weekly task due 10 days ago, finished today | 3 days ago ❌ | 3 days ago ❌ | in 7 days ✅ |
| One-time task | `None` ✅ | `None` ✅ | `None` ✅ |
| A new field added to `Task` later | dropped ❌ | kept ✅ | kept ✅ |
| Frequency typed as "Daily" | silently treated as one-time ❌ | works ✅ | rejected when the task is created ✅ |

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | Claude Haiku (through Claude Code) | Claude Sonnet (through Claude Code) |
| **Prompt** | The same prompt for both: "Here is my `Task` dataclass. Write `next_occurrence(self) -> Task \| None`. Daily tasks come back the next day, weekly tasks in 7 days, 'once' tasks return None. The new copy should not be marked complete. Handle any edge cases you think matter." | Same as Option A |
| **Response summary** | An `if`/`elif` on the frequency that adds 1 or 7 days to `due_date`, then builds a brand-new `Task(...)` by passing every field by hand. Unknown frequencies return `None`. | A small lookup table (`{"daily": 1 day, "weekly": 7 days}`) plus `dataclasses.replace(self, due_date=..., completed=False)`. Lowercases the frequency first, and returns `None` for anything not in the table. |
| **What was useful** | Very easy to read. A beginner can follow every line. | `replace()` copies every field automatically, so it can't fall out of date. Best of all, its explanation pointed out the late-task problem by itself, and suggested `max(self.due_date, date.today()) + delta` as the fix. It also noted that `timedelta` handles month and leap-year rollovers. |
| **Problems noticed** | Counts from the old due date, so a task finished late comes back already overdue, and it never mentions this. Listing every field by hand means a field added later would silently get dropped (my test confirmed this). "Daily" with a capital D quietly turns into a one-time task, which hides typos. | Also counts from the old due date by default, so it has the same overdue problem out of the box (it just warned about it). Quietly treating unknown frequencies as one-time can hide typos too. |
| **Decision** | Not used. | Its structure and its suggested fix are what I kept. |

**Which approach did you use in your final implementation and why?**

I kept my existing `next_occurrence()`, which turned out to be basically Sonnet's answer plus the fix Sonnet itself suggested. It uses `dataclasses.replace()` and counts from `max(self.due_date, date.today())`. That means a late task comes back tomorrow (or next week), not on a date that's already gone. That matters for a pet owner: if you skip the walk for a few days, you want it on today's list, not buried in the past.

I didn't need Sonnet's lowercasing, because my `Task` already rejects any frequency that isn't exactly "once", "daily", or "weekly" when the task is created. A typo fails loudly instead of quietly changing behavior.

The bigger lesson: both models wrote code that looked correct and passed the easy cases. The difference only showed up when I tested the late-task case and the "add a field later" case. Sonnet's answer was better mainly because it *explained its tradeoff*, which let me make an informed choice.
