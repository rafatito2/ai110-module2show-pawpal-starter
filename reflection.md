# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

Before drawing anything I wrote down the three things a pet owner actually needs to do in the app:

1. **Add a pet** to their profile (name, species, age) so tasks have somebody to belong to.
2. **Schedule a care task** for a pet: what it is, what time, how long it takes, how important it is, and whether it repeats (once / daily / weekly).
3. **See today's schedule** across all pets in time order, with warnings when two tasks collide, and mark tasks done so repeating ones roll forward to the next day or week.

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

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

Conflict detection only looks at one calendar day at a time and treats every task as starting exactly at its listed time and running exactly `duration_minutes`. A 30 minute walk at 18:30 and a vet visit at 18:45 get flagged, which is what I want, but a task at 23:50 that runs 20 minutes never gets compared with 00:05 the next day, and the scheduler has no idea that "feed Luna" and "feed Mochi" at the same time are actually fine because they take ten seconds each. I also flag conflicts for different pets, not just the same pet, since one person is doing all of it.

I think that's reasonable for this scenario. The owner is a single human, so two overlapping blocks really are a problem no matter which pet they belong to. Midnight-crossing tasks are rare for pet care, and making the check smarter (travel time, tasks that can run in parallel) would mean adding attributes the spec never asked for. The warning is advisory anyway, nothing gets blocked, so a false positive costs the user one glance.

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
