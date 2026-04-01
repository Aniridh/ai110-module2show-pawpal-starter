# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I started with four classes. `Task` holds everything about one care activity — what it is, when it's scheduled, how long it takes, and whether it's done. `Pet` keeps track of a single animal and its list of tasks. `Owner` sits on top of that and holds all the pets. `Scheduler` is the one that does the actual thinking: sorting, filtering, finding conflicts, generating the daily plan.

I kept it pretty flat on purpose. Each class has one clear job and doesn't know too much about the others. `Task` doesn't know about `Pet`, `Pet` doesn't know about `Owner`, and `Scheduler` just takes an `Owner` and works from there.

**b. Design changes**

My original sketch had recurrence logic inside `Scheduler` — the idea was that the scheduler would create the next task when you mark one complete. But then I realized `Task` already has all the information it needs to create its own next occurrence (frequency, due date, description, etc.). Moving `mark_complete()` onto `Task` so it returns a new `Task` (or `None` for one-time tasks) made a lot more sense. It also made the recurrence logic way easier to test on its own.

I also dropped a `priority` field I had in early sketches. I figured for a daily care schedule, time ordering is more practical — you look at the clock, not a priority number. Skipping your dog's morning walk is bad regardless of whether it's flagged "high" or "medium."

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler mainly cares about three things: the scheduled time (HH:MM), the due date, and whether the task is already done. `generate_daily_plan()` only shows tasks due today or earlier, and it leaves out anything already completed. Everything is sorted chronologically so the owner just reads top to bottom.

I also scoped conflict detection per-pet. If two different pets have something at the same time, that's totally fine — the owner can handle them separately. But the same pet can't physically be in two places, so that's the case worth flagging.

**b. Tradeoffs**

The conflict detection only catches exact time matches, not overlapping durations. So two tasks at `07:30` and `07:45` for the same pet won't trigger a warning even if the first one takes 30 minutes. I kept it this way because most pet care tasks are short and loosely spaced, and duration-overlap detection would require a lot more complexity for a marginal benefit in a basic scheduler. The exact-match check catches the most common mistake (accidentally scheduling two things at the identical time) without generating false alarms. I noted this as a known limitation in the test comments.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI (Claude Code) pretty heavily throughout this project, but in different ways for different phases. For the initial design, I described the scenario and asked it to sketch out a class diagram — that gave me a starting point to react to and trim down. It included a `Notification` class and some preference model that felt over-engineered, so I cut those.

For the actual logic, I found it most useful to ask narrow, specific questions. Something like "given this Task dataclass with a `frequency` field, how should `mark_complete()` return the next occurrence?" got me directly usable code. Broad questions like "write me a scheduler" produced generic stuff that needed heavy editing.

The test suite was another place AI helped a lot — I asked for a test plan covering sorting, recurrence, and conflict detection edge cases, and used that as a checklist to write tests myself rather than just copy-pasting AI-generated tests I hadn't read carefully.

**b. Judgment and verification**

At one point the AI suggested storing tasks in a dictionary keyed by task ID inside `Pet` instead of a list. The argument was faster lookup. I thought about it for a minute and decided against it — we're talking about fewer than 20 tasks per pet in any realistic scenario, so O(n) search is essentially instant. More importantly, a list preserves insertion order, which matters for how tasks appear before you sort them, and plain lists are easier to serialize in Streamlit's session state. Sometimes the "more efficient" data structure just adds friction without solving a real problem at this scale.

---

## 4. Testing and Verification

**a. What you tested**

The test suite has 18 tests spread across task completion, sorting, recurrence, conflict detection, filtering, and daily plan generation. I focused on behaviors that are easy to get subtly wrong — like making sure a daily task completion adds the next occurrence to the right pet (not just creates a floating Task object that never gets attached), or verifying that two pets sharing a time slot doesn't get flagged as a conflict when it shouldn't be.

Those tests matter because if any of them are broken, the UI will just silently show wrong data. A quick click-through in the browser wouldn't catch a bug where recurring tasks aren't being attached correctly.

**b. Confidence**

★★★★☆ — All 18 pass. The main gap is input validation: I never tested what happens if someone enters `"7:5"` or `"noon"` as a time. The sort would silently produce wrong order without any error. Adding validation in `Task.__post_init__` and testing that would be my next priority. I'd also add a test for a future-dated task to confirm it stays out of today's plan until the due date actually arrives.

---

## 5. Reflection

**a. What went well**

Running `main.py` in the terminal before touching the Streamlit UI at all was probably the best decision I made. It meant I had a working, tested backend before dealing with session state and rerenders. When I did start wiring the UI, I already knew the logic was correct, so any bug had to be in the rendering layer, which made debugging much faster.

**b. What you would improve**

Two things: duration-aware conflict detection (overlapping intervals instead of just exact matches), and input validation on `Task` so bad time strings fail loudly at construction time rather than causing weird sort behavior downstream. I'd also think about adding a simple priority field back in — maybe just for medications versus non-critical tasks, since those really shouldn't get buried if everything else is scheduled at the same time.

**c. Key takeaway**

Specific prompts work way better than vague ones. "Write the scheduler" gives you something generic. "Given this method signature and this data model, implement the daily vs. weekly recurrence case" gives you something you can actually use. The more precisely I could describe what I needed — including the constraints and what I'd already ruled out — the less editing the AI output needed. The back-and-forth gets faster once you learn to front-load the context.
