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

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
