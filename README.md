# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Here's what `python main.py` prints. The demo owner has two pets, eight tasks, and 90 minutes for pet care. The tasks are added out of order on purpose, and two of them start at 07:30, so you can see the sorting and the conflict warning:

```
Today's Schedule for Jordan (Saturday, October 03)
----------------------------------------------------------------
07:30-08:00  Morning walk       Mochi  high
07:30-07:45  Call the vet       Luna   high
08:00-08:10  Breakfast          Mochi  high
08:15-08:20  Breakfast          Luna   high
09:00-09:05  Flea medicine      Luna   medium
19:00-19:15  Brush coat         Luna   medium
----------------------------------------------------------------
Planned 6 task(s) using 80 of 90 available minutes.
Higher-priority tasks were picked first, then the plan was put in time order.
Skipped: Fetch in the yard for Mochi (45 min, low priority), not enough time left.

Conflict check
----------------------------------------------------------------
WARNING: Mochi's Morning walk (07:30-08:00) overlaps with Luna's Call the vet (07:30-07:45).

Recurring tasks
----------------------------------------------------------------
Done: Morning walk (Mochi, daily) -> next one added for Sun Oct 04
Done: Flea medicine (Luna, weekly) -> next one added for Sat Oct 10
Done: Call the vet (Luna, once) -> doesn't repeat, nothing added

Filter: Mochi's tasks
----------------------------------------------------------------
Sat Oct 03  07:30-08:00  Morning walk       Mochi  high    done
Sat Oct 03  08:00-08:10  Breakfast          Mochi  high
Sat Oct 03  17:00-17:45  Fetch in the yard  Mochi  low
Sun Oct 04  07:30-08:00  Morning walk       Mochi  high

Filter: finished tasks
----------------------------------------------------------------
Sat Oct 03  07:30-08:00  Morning walk       Mochi  high    done
Sat Oct 03  07:30-07:45  Call the vet       Luna   high    done
Sat Oct 03  09:00-09:05  Flea medicine      Luna   medium  done
```

A few things to notice:

- The 45-minute fetch session was the only low-priority task, and it didn't fit in the 10 minutes left, so the scheduler skipped it and said why.
- The walk and the vet call both start at 07:30, so the conflict check flags them. Breakfast at 08:00 isn't flagged, because the walk ends right as it starts.
- Finishing the daily walk adds a new walk for tomorrow, and finishing the weekly flea medicine adds one for next week. The one-time vet call just gets marked done.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

These are the parts of the `Scheduler` (and `Task`) that make the plan smarter than a plain to-do list. All of them live in `pawpal_system.py`.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` | `sort_by_time()` orders tasks by due date, then start time, using `sorted()` with a lambda key. `sort_by_priority()` puts high before medium before low, with earlier tasks winning ties. |
| Daily plan | `Scheduler.build_daily_plan()`, `Scheduler.explain_plan()` | Picks today's unfinished tasks by priority until the owner's available minutes run out, then puts the plan in time order. Anything that doesn't fit goes in `scheduler.skipped`, and the explanation says why. |
| Filtering | `Scheduler.filter_tasks(pet_name=..., completed=...)` | Shows one pet's tasks, only finished or unfinished tasks, or both at once. Leave an argument out to skip that filter. |
| Conflict handling | `Scheduler.detect_conflicts()` | Flags any two tasks on the same day whose time ranges overlap, not just exact matches. It returns warning messages instead of raising errors, so the app keeps running and the owner decides what to move. |
| Recurring tasks | `Scheduler.complete_task()`, `Task.next_occurrence()` | Marking a daily or weekly task done adds a fresh copy for tomorrow or next week, using `timedelta`. A late task comes back starting from today, so it never lands on a date that's already gone. Marking the same task done twice doesn't make duplicates. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
