# Course Blueprint: Agent Engineering from Runtime to Production — V2

## 1. North Star

The learner should finish the course able to **design, implement, debug, evaluate, and productionize an Agent system without depending on a framework's abstractions to understand what is happening**.

This is a capability-construction course, not a framework survey.

## 2. Canonical Definition

The course uses the definition in `docs/ONTOLOGY.md`:

> An Agent is a stateful runtime controller that pursues a TaskSpec by repeatedly observing its environment, constructing decision context, selecting actions through a policy (often model-backed), updating state, and terminating according to explicit success, failure, or budget conditions.

## 3. The Runtime Questions

For every Agent run, the learner must be able to answer:

1. What is the task and what counts as success?
2. What did the Agent observe?
3. What state is being carried forward?
4. What information entered the model context?
5. What policy produced the next decision?
6. What action was allowed and executed?
7. How did the state transition?
8. Why did the run continue or stop?
9. How do we know the outcome is correct?

## 4. Course Structure

| Module | Theme | Main Artifact |
|---|---|---|
| M0 | Agent System Mental Model | runtime decomposition |
| M1 | Model Runtime & Structured Interaction | model adapter |
| M2 | Tools & Action Interfaces | tool registry/executor |
| M3 | State, Control Loop & Termination | explicit agent runtime |
| M4 | Evaluation, Tracing & Failure Analysis | trace + eval harness |
| M5 | Context Engineering & Working State | context builder |
| M6 | Retrieval, Grounding & Evidence | retrieval/evidence layer |
| M7 | Memory & Persistence | checkpoint + memory policy |
| M8 | Planning, Workflows & Human Control | planner/workflow/HITL |
| M9 | Delegation, Multi-Agent & Protocols | composition layer |
| M10 | Safety, Reliability & Resource Control | guardrails/budgets/reliability |
| M11 | Production Delivery & Operations | deployable service + ops |
| Capstone | Project Understanding Agent | complete production-style system |

See `CURRICULUM_MAP.md` for lesson-level topics.

## 5. Course Architecture

The curriculum is divided into four conceptual planes:

- **Runtime plane:** the minimal state transition loop.
- **Capability plane:** retrieval, memory, planning, human control, delegation.
- **Interoperability plane:** tool APIs, MCP, agent-to-agent protocols.
- **Assurance/operations plane:** evaluation, tracing, safety, reliability, cost, deployment.

This prevents implementation techniques from being confused with core Agent primitives.

## 6. Learning Progression

### Stage 0 — Foundations: M0–M1
Understand the system boundary and model runtime.

### Stage 1 — Minimal Agent: M2–M3
Build an explicit tool-using stateful control loop.

### Stage 2 — Measurement: M4
Instrument and evaluate the minimal system before adding complexity.

### Stage 3 — Information & Knowledge: M5–M7
Build context selection, evidence-backed retrieval, and persistence.

### Stage 4 — Control Architecture: M8
Choose between reactive agents, plans, workflows, and human checkpoints.

### Stage 5 — Composition: M9
Compose specialized capabilities and agents only when the single-agent baseline is insufficient.

### Stage 6 — Production: M10–M11
Add safety, reliability, resource controls, delivery, monitoring, and operations.

## 7. Cumulative Reference Implementation

One reference implementation evolves through the entire course. No module should create an unrelated toy architecture.

Target structure:

```text
reference_agent/
  pyproject.toml
  .env.example
  src/agent_course/
    core/
      task.py
      observation.py
      state.py
      decision.py
      transition.py
      termination.py
    llm/
    context/
    tools/
    runtime/
    evals/
    tracing/
    retrieval/
    memory/
    planning/
    human/
    composition/
    protocols/
    safety/
    reliability/
    api/
  tests/
  evals/
  examples/
```

## 8. Standard Teaching Pattern

Every major concept follows:

1. Problem
2. Definition
3. System boundary
4. Runtime mechanism
5. Minimal implementation
6. Trace walkthrough
7. Failure modes
8. Evaluation method
9. Engineering rule
10. What changed in our reference Agent?

## 9. Standard Module Deliverables

Each module must contain:

- `chapter.md`
- `lab/README.md`
- runnable code
- tests
- `exercises.md`
- `quiz.md`
- `quiz_answers.md`
- at least one trace/example
- at least one new or updated eval case after M4

## 10. Capstone

Default: **Project Understanding Agent**.

It must demonstrate:
- explicit TaskSpec and success criteria
- repository exploration tools
- stateful exploration loop
- context selection
- evidence/provenance
- plan/replan or justified workflow
- budget/termination policy
- trace logs
- evaluation fixtures
- single-agent baseline
- optional justified delegation
- safety around file/shell tools
- CLI/API delivery

The final report must clearly distinguish **evidence**, **inference**, **uncertainty**, and **recommendation**.
