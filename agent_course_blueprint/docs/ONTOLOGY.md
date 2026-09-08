# Agent Engineering Ontology

This file freezes the course-wide conceptual model. OpenCode must not redefine these terms silently.

## 1. System Boundary

An agent is not the whole world it interacts with.

```text
Task / User
    |
    v
+----------------------------- AGENT RUNTIME -----------------------------+
| TaskSpec -> State -> Context -> Policy/Model -> Decision -> Action      |
|                 ^                                      |                |
|                 |                                      v                |
|             Transition <-------- Observation <---- Tool Result           |
|                                                                    |    |
|                    Control + Termination + Budgets                  |    |
+--------------------------------------------------------------------|----+
                                                                     v
                                                              Environment
```

The **Environment** is outside the agent boundary. Files, databases, browsers, APIs, shells, users, and other agents may all be part of the environment.

Tools are controlled interfaces through which the runtime reads from or acts on the environment.

## 2. Core Runtime Objects

### TaskSpec
Defines what the run is trying to accomplish.

Minimum fields:
- goal
- success criteria
- constraints
- available budget
- optional output contract

### Observation
New information available to the runtime at a particular step.

Examples:
- user input
- tool output
- environment event
- human approval/rejection
- error

### State
The explicit information carried from one step to the next.

State is broader than chat history. It may contain:
- task progress
- tool results
- plan
- evidence
- open questions
- budgets
- status
- intermediate artifacts

### Context
The selected representation given to a model for one model call.

Context is a **view constructed from other information**, not a synonym for all state.

Typical inputs to context construction:
- TaskSpec
- instructions/policies
- selected State
- current Observation
- tool/capability descriptions
- retrieved information
- memory records

### Model
A probabilistic computation engine used by one or more runtime components.

The model does not equal the whole agent. It may be used to implement the policy, planning, summarization, classification, evaluation, or other subroutines.

### Policy
The rule that maps the current runtime situation to the next decision.

Conceptually:

```text
Decision_t = Policy(TaskSpec, State_t, Observation_t, Context_t)
```

A policy can be:
- deterministic code
- an LLM
- an LLM constrained by deterministic code
- a router or ensemble

### Decision
A typed runtime choice produced by the policy.

Examples:
- call tool X with arguments Y
- ask the user a question
- update/revise the plan
- delegate a subtask
- emit a final answer
- stop with a failure state

### Action
A validated side effect or information-acquisition operation executed against the environment.

### Tool
A named, schema-defined action adapter available to the runtime.

A tool is not inherently agentic. The agentic behavior comes from runtime decision-making about whether, when, and how to invoke actions.

### Transition
The deterministic or controlled update from the current state to the next state.

```text
State_(t+1) = Transition(State_t, Observation_t, Decision_t, ActionResult_t)
```

### Control Loop
The mechanism that sequences observations, decisions, actions, state transitions, and repeated execution.

### Termination
The policy that decides when the run must stop.

Termination can depend on:
- success criteria
- explicit final decision
- max steps
- token/cost/time budget
- unrecoverable error
- human stop

## 3. Canonical Runtime Equation

Each step should be explainable as:

```text
O_t   = observe(environment, previous_action)
C_t   = build_context(task, state_t, O_t, capabilities)
D_t   = policy(model, C_t)
R_t   = validate_and_execute(D_t, tools, permissions)
S_t+1 = transition(S_t, O_t, D_t, R_t)
STOP  = termination(task, S_t+1, budgets)
```

If `STOP == false`, the next iteration begins.

## 4. Four Conceptual Planes

### A. Runtime Plane
The minimal machinery required for an agent run:
- TaskSpec
- Observation
- State
- Context
- Policy / Model
- Decision
- Action / Tools
- Transition
- Control / Termination

### B. Capability Plane
Extensions that improve what the runtime can do:
- retrieval and evidence grounding
- durable memory
- planning and replanning
- human approval
- delegation
- multi-agent composition

These are not all required for every agent.

### C. Interoperability Plane
Standard interfaces that connect the runtime to external capability ecosystems or other agents:
- tool APIs
- MCP-style context/tool integration
- agent-to-agent protocols such as A2A

Protocols are interfaces, not definitions of an agent.

### D. Assurance / Operations Plane
Cross-cutting engineering mechanisms:
- evaluation
- tracing / observability
- safety / permissions
- security
- reliability
- latency / cost control
- deployment
- versioning and rollout

These should be taught throughout the course, not treated as optional polish.

## 5. Important Non-Equivalences

- LLM != Agent
- Prompt != Context
- Chat history != State
- State != Memory
- Retrieval != Memory
- RAG != Agent
- Tool calling != Agent
- Workflow != Agent, although a workflow may contain agentic nodes
- Multi-agent != automatically better agent
- MCP != multi-agent protocol
- A2A != tool protocol
- Successful execution != correct execution

## 6. Definition Used by This Course

> An **Agent** is a stateful runtime controller that pursues a TaskSpec by repeatedly observing its environment, constructing decision context, selecting actions through a policy (often model-backed), updating state, and terminating according to explicit success, failure, or budget conditions.

This definition is intentionally implementation-independent.
