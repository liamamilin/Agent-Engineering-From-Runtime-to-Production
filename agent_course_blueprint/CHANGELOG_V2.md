# V2 Architecture Revision

Major changes from the initial blueprint:

1. Added **TaskSpec / Goal / Success Criteria** as first-class runtime concepts.
2. Moved **Environment** outside the Agent system boundary.
3. Separated **Model** from **Policy**.
4. Defined explicit Observation, Decision, Transition, and Termination objects.
5. Moved Evaluation/Observability to a cross-cutting assurance plane and moved its dedicated module earlier.
6. Reclassified Retrieval, Memory, Planning, and Multi-Agent as capability/composition extensions rather than core primitives.
7. Separated protocol concerns: MCP for capability/context integration; A2A-style protocols for agent-system interoperability.
8. Added explicit planning/workflow/human-control module.
9. Split production concerns into safety/reliability/resource control and delivery/operations.
10. Expanded curriculum from M0–M9 to M0–M11.
