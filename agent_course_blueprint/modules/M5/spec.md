# M5 Spec — Context Engineering & Working State

## Build
Budget-aware `ContextBuilder` with inspectable selection policy.

## Must Teach
- Context as per-call selected view
- difference among instructions, task, state, observation, memory, retrieved data, tool descriptions
- budget allocation and priority
- truncation vs selection vs compaction
- summarization tradeoffs
- prompt injection boundaries
- context debugging and observability
- context cache/reuse conceptually

## Lab Acceptance
- context selection is deterministic in offline test mode
- budget overflow behavior is tested
- selected/dropped items are traceable
- malicious retrieved text is separated from trusted instructions
