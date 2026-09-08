# M7 Spec — Memory & Persistence

## Build
Checkpoint store plus explicit memory write/read/forget policies.

## Must Teach
- transient runtime state
- session state
- checkpointing/resume
- durable memory
- episodic / semantic / user memory
- memory write policy
- memory retrieval policy
- forgetting and invalidation
- freshness and conflict handling
- privacy/data boundaries

## Lab Acceptance
- interrupted run can resume from checkpoint
- memory write is not automatic for every message
- stale memory can be invalidated
- memory retrieval is observable in traces
