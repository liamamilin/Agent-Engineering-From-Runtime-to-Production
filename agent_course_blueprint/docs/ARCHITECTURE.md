# Canonical Agent Architecture — V2

Read `docs/ONTOLOGY.md` first. This architecture is the implementation view of that ontology.

```text
                         +--------------------+
                         |      TaskSpec      |
                         | goal / criteria /  |
                         | constraints/budget |
                         +---------+----------+
                                   |
                                   v
+-----------------+       +--------+---------+       +-------------------+
| Observation     |------>| Context Builder  |<----->| Runtime State     |
| user/tool/event |       | selected view    |       | progress/evidence |
+--------+--------+       +--------+---------+       +---------+---------+
         ^                         |                           ^
         |                         v                           |
         |                +--------+---------+                 |
         |                | Policy / Model  |                 |
         |                +--------+---------+                 |
         |                         | Decision                  |
         |                         v                           |
         |                +--------+---------+                 |
         |                | Decision Validator|                |
         |                +--------+---------+                 |
         |                         |                           |
         |                         v                           |
         |                +--------+---------+                 |
         |                | Tool / Action    |-----------------+
         |                | Executor         |  transition     |
         |                +--------+---------+                 |
         |                         |                           |
         |                         v                           |
         |                  Environment                       |
         +---------------------- result -----------------------+

Controller wraps the loop:
- step sequencing
- retries/fallbacks
- budgets
- human checkpoints
- termination

Cross-cutting assurance plane:
- tracing
- evaluation
- safety / permissions
- reliability
- cost / latency
- versioning
```

## Minimal Runtime Types

```python
from dataclasses import dataclass, field
from typing import Any, Literal

@dataclass
class TaskSpec:
    goal: str
    success_criteria: list[str]
    constraints: list[str] = field(default_factory=list)
    max_steps: int = 20
    max_cost_usd: float | None = None

@dataclass
class Observation:
    kind: str
    payload: Any

@dataclass
class Decision:
    kind: Literal["tool", "ask_user", "final", "fail"]
    name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    content: Any = None

@dataclass
class AgentState:
    task: TaskSpec
    step_count: int = 0
    status: str = "running"
    observations: list[Observation] = field(default_factory=list)
    tool_results: list[Any] = field(default_factory=list)
    working: dict[str, Any] = field(default_factory=dict)
    evidence: list[Any] = field(default_factory=list)
    final_output: Any | None = None
```

## Canonical Step Contract

The course reference implementation should make this flow visible rather than hiding it behind a framework:

```python
observation = observe(...)
context = context_builder.build(task, state, observation, capabilities)
decision = policy.decide(context)
validated = decision_validator.validate(decision)
result = action_executor.execute(validated)
next_state = transition(state, observation, validated, result)
stop = termination.should_stop(task, next_state)
```

## Design Rule

The learner should always be able to answer:

1. What is the TaskSpec?
2. What is currently in State?
3. What new Observation arrived?
4. What exactly entered model Context?
5. Which component produced the Decision?
6. What Action was executed?
7. How did State change?
8. Why did the loop continue or terminate?

If these cannot be answered from a trace, the implementation is too opaque for this course.
