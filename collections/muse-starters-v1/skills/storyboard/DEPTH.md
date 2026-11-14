# Build a Storyboard With Clear Shot Purpose — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

A storyboard is a sequence of motivated visual decisions, not a list of attractive frames. Give each shot a story purpose, first-frame state, physically possible action, duration, screen direction and transition. Track character, prop and spatial continuity across cuts. Translate emotion into observable behavior. Budget action beats against time and distinguish intentional discontinuity from accidental inconsistency.

## Output contract

Deliver stable shot IDs, durations, action beats, camera/composition, dialogue or sound where requested, continuity inputs/outputs and transition intent. The timeline must fit the requested duration and preserve required story beats. A storyboard is not a rendered video.

## Choose the right action

### A shot contains more actions than its duration plausibly supports.
Simplify to the essential beat or split the shot within the total duration.

**Avoid:** Do not compress a complex performance into an impossible time block.

### A cut reverses screen direction.
Check the geography and crossing rule; add a motivated reorientation or preserve the axis.

**Avoid:** Do not label an accidental reversal a stylistic choice after the fact.

### A recurring prop changes hands.
Specify the handoff or off-screen transition explicitly and carry its state forward.

**Avoid:** Do not reset prop ownership independently in every shot.

### The user already approved assets and geography.
Use those records and proceed to shot direction.

**Avoid:** Do not reopen the concept interview or invent a new cast.

### The request is for a finished clip.
Treat the storyboard as an intermediate artifact and continue through an available authorized production route.

**Avoid:** Do not claim the storyboard itself is the requested video.

## Worked example (authored, synthetic)

**Input:** A 12-second sequence at 24 fps has three shots: approach 4 s, discover 5 s, reaction 3 s, with hard cuts. A key remains in the character's left hand.

**Method:** Allocate 96, 120 and72 frames; carry the left-hand key state through both cuts.

**Result:** The storyboard totals 288 frames. Each shot has one clear purpose and the key remains in the left hand unless a documented handoff occurs.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The same three durations now use two one-second overlapping dissolves.

**Method:** Subtract 48 overlap frames from the 288 shot frames; the delivery would be 240 frames, not 288.

**Result:** Either extend holds by 48 frames or change the transitions. Do not call the current timeline 12 seconds; it is 10 seconds at 24 fps.

## Failure diagnosis

### The timeline exceeds the requested length.
**Likely cause:** Transition overlap or hold frames were omitted from the sum.

**Repair:** Recompute the exact frame total and revise the least important hold or beat.

**Recheck:** Shot durations minus overlaps equal the target within the stated tolerance.

### A character or prop appears without an entry.
**Likely cause:** Each shot was designed independently of the preceding state.

**Repair:** Add a visible or explicitly motivated transition and recheck adjacent shots.

**Recheck:** Every continuity-sensitive change is accounted for.

### The prompt says only that a character feels worried.
**Likely cause:** Emotion was not translated into observable performance.

**Repair:** Specify gaze, hesitation, breath, posture or action tied to the scene objective.

**Recheck:** The performance can be staged without inferring an invisible mental label.

## Preserve for the next turn

Preserve the shot IDs, story beat map, frame rate, durations, overlap rules, geography and continuity state. Resume the unverified shot or transition without redesigning accepted assets or claiming unrendered footage.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `storyboard-r3-standard`, `storyboard-r3-edge`, `storyboard-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.
