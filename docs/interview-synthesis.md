# Interview Synthesis - Open-Time Listeners

> **Segment:** Open-Time Listeners - people who listen during unstructured time (evenings, weekends, no fixed task) and have tried Discover Weekly or a recommendation feature at least a few times but stopped actively engaging with it.

## Screening Criteria (Behavior, Not Demographics)

1. "Do you listen during open/unstructured time - evenings or weekends without a fixed task?"
2. "Have you tried Discover Weekly or recommendations more than twice?"
3. "Did you stop actively engaging after one or more bad experiences?"

## Interview Summaries (9 Participants)

| Name | Frequency | Discovery Engagement | Trust in Recs | Would "Why" Help? | Segment Fit |
|---|---|---|---|---|---|
| **Srivatsan** | Multiple/day | Curated playlists, DW | Skeptical, skips | Trust a lot more | **Target**: Frustrated Discoverer |
| **Sakthi** | Multiple/day | Active discoverer | Trusts, listens | Slightly more | **Target**: Satisfied but curious |
| **Syed** | Few times/week | Replays only | Skeptical, disengaged | Trust a lot more | **Target**: Churned Discoverer |
| **Radhika** | Multiple/day | Active discoverer | Skims/skips | Slightly more | **Target**: Satisfied Discoverer |
| **Arun** | Multiple/day | Active discoverer | Skims/skips | Slightly more | **Target**: Context-Seeking Discoverer |
| **Jonathan** | Few times/week | DW ritualist | Trusts, listens | Trust a lot more | **Target**: Active Discoverer wanting depth |
| **Gourav** | Few times/week | Discovers + background | Skims/skips | Slightly more | **Target**: Inconsistency-Frustrated |
| **Tej** | Once/day | Background, replays | Trusts, passive | No difference | *Non-Target*: Passive Replayer |
| **Praveen** | Once/day | Replays, podcasts | Skeptical | No difference | *Non-Target*: Utility-Only User |

## Validation Matrix

| RDE Theme | Interview Result | Confidence | Build Against? |
|---|---|---|---|
| **One miss -> weeks of distrust** | 7/9 Strong (Srivatsan, Syed, Gourav, Jonathan, Radhika, Arun, Sakthi) | ⬛⬛⬛⬛⬛ | ✅ Yes - repair mechanism |
| **No explain-why = no engagement** | 8/9 Strong | ⬛⬛⬛⬛⬛ | ✅ Yes - "Why This" line |
| **Moment vs. long-term taste** | 6/9 Moderate/Strong | ⬛⬛⬛⬛⬜ | ✅ Yes - context awareness |
| **Echo chamber / repetition** | 5/9 Moderate | ⬛⬛⬛⬜⬜ | ✅ Yes - novelty adjustment |
| **Social proof** | 2/9 Weak | ⬛⬛⬜⬜⬜ | ❌ No - deprioritize |

## What Confirmed

**Confirmed strongly (7-8 of 9):**
- A single bad recommendation has an outsized, lingering effect on trust. (Syed: "That single bad week made me lose trust entirely - I haven't opened it since")
- Absence of any explanation for why a track was picked is a real, repeated frustration. (Srivatsan: "Just tell me WHY you picked something")

**Confirmed moderately (5-6 of 9):**
- Desire for recommendations connected to "right now" vs. long-term taste. (Arun: "On a Sunday evening when I'm winding down, I don't want the high-energy workout music")
- The echo chamber effect where algorithms latch onto one specific genre/taste profile and over-index it. (Srivatsan: "my entire Discover Weekly is nothing but Tamil indie for three weeks straight")

**Not confirmed as primary:**
- Social discovery need (friends' playlists) - appeared in Reddit RAG data more than interviews. Not building around it as primary need.
- Discovery features for utility listeners (Tej, Praveen) - they self-selected out, confirming the boundaries of our target segment.

## Design Implications

1. **Repair mechanism is non-negotiable.** 7/9 participants confirmed that a single bad recommendation costs weeks of disengagement. The system must have a way to recover.
2. **Explanation is the minimum viable trust signal.** Even one sentence ("picked because you've been playing high-BPM tracks this week") would increase listen-through time.
3. **Context must be acknowledged.** The system needs to allow users to override long-term history with immediate mood (e.g., gym vs commute).
4. **Targeting matters.** We are building for the 7 active/frustrated discoverers, not the 2 utility users who view Spotify solely as a jukebox.
