# M0 Spec — Agent System Mental Model

## Learning Objectives
- distinguish LLM call, workflow, tool-using workflow, and Agent
- draw the system boundary correctly
- define TaskSpec, Observation, State, Context, Policy, Decision, Action, Transition, Termination, Environment
- explain where Model and Tools fit without equating them to the whole Agent
- classify common failures by layer

## Required Chapter Topics
- canonical definition from `docs/ONTOLOGY.md`
- autonomy as a spectrum
- deterministic vs probabilistic components
- one traced end-to-end Agent step
- system boundary examples
- non-equivalences (RAG != Agent, MCP != multi-agent, etc.)

## Required Exercise
Given three systems, classify each as LLM call, workflow, or Agent and draw the runtime objects and boundary.

## Acceptance
Learner can narrate a run using the canonical runtime equation without framework terminology.
