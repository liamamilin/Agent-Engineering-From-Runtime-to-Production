# Reference Implementation Evolution

The learner modifies one runtime throughout the course.

| Module | Runtime Change |
|---|---|
| M0 | typed pseudocode and trace schema |
| M1 | provider-independent model interface + fake model |
| M2 | tool registry, schemas, validator, executor |
| M3 | TaskSpec, State, Decision, Transition, termination, loop |
| M4 | structured traces, eval dataset, replay harness |
| M5 | explicit ContextBuilder with token/budget policy |
| M6 | retrieval tool, Evidence object, provenance/grounding checks |
| M7 | checkpoints, durable store, memory write/read/forget policy |
| M8 | plan object, workflow/state-machine option, human approval/resume |
| M9 | agent-as-tool/handoff/composition + protocol adapter example |
| M10 | permissions, guardrails, sandbox boundary, budgets, reliability |
| M11 | API/CLI, config, sessions, monitoring hooks, deployment artifacts |

## Architectural Constraint

Framework adapters may be added only after the plain runtime exists. The plain runtime remains the source of truth for teaching execution semantics.
