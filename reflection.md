# PawPal+ Project Reflection

## 1. System Design

**Core actions**

These are the three main things a user should be able to do in PawPal+:

1. **Add a pet.** The owner enters their name and how much time they have for pet care today, then adds a pet with its name, species, and age. One owner can have more than one pet.
2. **Add a care task for a pet.** The owner picks a pet and adds a task like a walk, a feeding, or meds. Each task has a start time, how long it takes, how important it is (low, medium, or high), and how often it repeats (once, daily, or weekly).
3. **See today's plan.** The app gathers today's tasks from every pet, puts them in order, warns about tasks that overlap, leaves out lower-priority tasks if there isn't enough time, and explains why the plan looks the way it does.

**a. Initial design**

My design has four classes. I kept the data classes small and put the "thinking" in one place, the Scheduler.

- **Task** holds the details of one care activity: what it is, when it starts, how long it takes, its priority, how often it repeats, the date it's due, and whether it's done. It can mark itself complete and make a copy of itself for the next day or week if it repeats.
- **Pet** holds basic info (name, species, age) and its own list of tasks. It can add and remove tasks and give back the ones that aren't done yet.
- **Owner** holds the owner's name, how many minutes they have for pet care each day, and their list of pets. It can add, remove, and look up pets, and collect every task from all of them into one list.
- **Scheduler** is the brain. It takes an Owner and works with all of their tasks: building the daily plan, sorting by time or priority, filtering by pet or status, finding time conflicts, handling repeat tasks when one gets marked done, and writing a short explanation of the plan.

The relationships are simple. An Owner has many Pets, a Pet has many Tasks, and the Scheduler reads from the Owner. I used Python dataclasses for Task, Pet, and Owner because they mostly hold data, and a regular class for Scheduler because it's mostly behavior.

The README also mentions owner preferences. I left those out for now. Time and priority are the two things that matter most for a daily plan, so I'm starting there and will add preferences later if I find one that actually changes the plan.

**b. Design changes**

Yes. After writing the skeleton, I asked the AI to review `pawpal_system.py` for missing relationships and logic problems. It found a few real issues, and I made these changes:

- **Tasks now know which pet they belong to.** In my first draft, a Task had no link back to its Pet. Once the Scheduler pulled every task into one list, there was no way to tell "Mochi's walk" from "Luna's walk," and filtering by pet wouldn't work. I added a `pet_name` field that `Pet.add_task()` fills in on its own.
- **`complete_task()` only needs the task now.** Since a task knows its pet's name, the Scheduler can find the right pet by itself when it needs to add the next copy of a repeat task. Before, the caller had to pass the pet in as well.
- **Priority sorts by rank, not by text.** Priority is stored as "low", "medium", or "high". Sorting those as plain words puts "high" first, then "low", then "medium," which is wrong. I added a `priority_rank()` method so sorting uses numbers instead.
- **The Scheduler remembers what it skipped.** When there isn't enough time, the Scheduler leaves out lower-priority tasks. My first draft just dropped them, so the explanation had no way to mention them. Now they go into a `skipped` list.
- **Removing a task uses the task itself, not its name.** A pet can have two tasks with the same name, like "Feeding" in the morning and at night, so removing by name could delete the wrong one.

One more change came up while I was building the classes: **an owner can't have two pets with the same name.** Tasks find their pet through `pet_name`, so two pets named "Mochi" would make that link unclear. `Owner.add_pet()` now stops you with a clear error instead.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

The biggest tradeoff is that **the scheduler picks tasks greedily by priority.** It goes down the list from high to low and adds each task if it still fits in the owner's time. It doesn't try every combination to find the "best" fit. That means it can leave some minutes unused. For example, if 20 minutes are left and the next task takes 30, it skips that task and moves on, even if two smaller tasks together would have been a better use of the time.

I think that's reasonable here. For a pet owner, the important part is that the high-priority stuff (meds, feeding, walks) always gets in first, and that the plan is easy to understand. "We did the important things first, and this one didn't fit" is something a person can follow and trust. A perfect packing algorithm would be harder to explain and would barely matter with the handful of tasks a person has in a day.

A second, smaller tradeoff: **conflicts are warnings, not fixes.** If two tasks overlap, the scheduler tells you, but it doesn't move anything. It does check full time ranges, not just exact start times, so a 2-hour hike that runs into a 9:00 med dose gets caught. But deciding what to move is left to the owner, since they know things the app doesn't (like whether the vet call can happen during the walk).

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

When I asked how to make `detect_conflicts()` simpler or faster, the AI suggested a shorter version: sort the tasks by time, then only compare each task to the one right after it. It looked cleaner and faster than checking every pair of tasks.

I didn't take it as-is, because I wasn't sure it caught everything. So I tested both versions on a tricky case: a 2-hour hike starting at 08:00, breakfast at 08:30, and meds at 09:00. The check-every-pair version found both overlaps (hike + breakfast, hike + meds). The shorter version only found one, because it never compared the hike to the meds. Those two aren't next to each other in the list.

I kept the check-every-pair version. It's easy to read, it's correct, and a pet owner might have 10 or 20 tasks in a day, so the speed difference doesn't matter at all. The lesson for me was that "shorter" and "more Pythonic" don't automatically mean "right." It's worth running a quick edge case before swapping in a suggestion.

---

## 4. Testing and Verification

**a. What you tested**

I wrote 28 tests covering the five things the app has to get right: sorting tasks by time, building a daily plan that fits the owner's time, bringing back daily and weekly tasks after they're done, catching overlapping tasks, and filtering by pet or status. I also tested the basic input checks, like rejecting a priority of "urgent" or a time like "25:00".

For each feature I tested the normal case and then the edge cases where bugs like to hide. Some examples: two tasks back to back (8:00 end, 8:00 start) should *not* count as a conflict, finishing the same task twice shouldn't create two copies of tomorrow's task, and a pet with no tasks should give an empty plan instead of crashing.

These tests matter because the scheduler makes decisions for the owner. If sorting or recurrence is quietly wrong, someone could miss a med dose and never know why. All 28 tests passed on the first run, which made me a little suspicious, so I broke the code on purpose in five different ways to see if the tests would notice. Each time, the right test failed. That told me the tests were actually checking something and not just passing by default.

**b. Confidence**

Pretty confident, about 4 out of 5. The core logic is well covered, and I know the tests can catch real mistakes. I'm not giving it a 5 because the Streamlit app itself isn't covered by automated tests (I checked it by clicking through it), and there are a few situations the code doesn't handle yet.

If I had more time, these are the edge cases I'd test next:

- A task that runs past midnight, like 23:30 for 60 minutes. Right now the conflict check wouldn't see it overlap with a 00:15 task the next morning.
- A task longer than the owner's whole time budget. It should get skipped with a clear reason, but I'd want a test that proves it.
- Removing a pet that still has tasks, or a repeat task whose pet was removed before the task was marked done.
- Tests that don't depend on today's date. A few of my tests use `date.today()`, so a test running right at midnight could flip a day.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
