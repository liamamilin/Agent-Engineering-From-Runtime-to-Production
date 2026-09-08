# Content Style Guide — V2

## Teaching Voice

- precise, engineering-oriented, concrete
- avoid hype and anthropomorphic explanations
- prefer runtime explanation over metaphor
- use Chinese as the primary explanatory language per `COURSE_CONFIG.yaml`
- introduce canonical English technical terms on first use

## Required Concept Pattern

1. Definition
2. Why it exists
3. Where it sits in the system boundary
4. Runtime mechanism
5. Minimal example
6. Trace/example state transition
7. Failure modes
8. Evaluation method
9. Engineering rule

## Code Rules

- plain Python before frameworks
- all code must run
- every lab includes tests
- model/network interactions must be mockable
- separate domain/runtime logic from provider logic
- use typed interfaces when they expose boundaries
- no hidden global state
- no API keys in code
- side-effecting actions require validation/permission controls

## Terminology

Use `docs/ONTOLOGY.md` as the source of truth.

Especially preserve:
- TaskSpec
- Observation
- State
- Context
- Model
- Policy
- Decision
- Action
- Tool
- Transition
- Control Loop
- Termination
- Environment
- Evaluation
- Trace

## Anti-Patterns

Do not:
- define Agent as "an AI that thinks and acts like a human"
- define Agent by a framework class
- treat tool calling alone as sufficient for Agent behavior
- equate RAG with Agent
- equate chat history with memory
- equate State and Context
- treat MCP as a synonym for multi-agent
- present multi-agent as automatically superior
- hide state transitions behind SDK magic
- treat successful execution as sufficient evidence of correctness
