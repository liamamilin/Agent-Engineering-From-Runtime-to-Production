# OpenCode Master Prompt

You are building the first complete draft of this Agent Engineering course repository.

## Mandatory Reading Order

1. `COURSE_CONFIG.yaml`
2. `docs/ONTOLOGY.md`
3. `COURSE_BLUEPRINT.md`
4. `CURRICULUM_MAP.md`
5. `docs/ARCHITECTURE.md`
6. `docs/FAILURE_MODEL.md`
7. `docs/REFERENCE_IMPLEMENTATION.md`
8. `CONTENT_STYLE_GUIDE.md`
9. `AGENT_INSTRUCTIONS.md`
10. `OPENCODE_TASKS.md`
11. relevant `modules/MXX/spec.md`

## Non-Negotiable Rules

- Do not redefine the ontology silently.
- Do not hide the runtime behind a framework.
- Build one cumulative `reference_agent/` implementation.
- Every model/network call must be mockable.
- Every lab must have runnable tests.
- After M4, every module must add or update evaluation cases.
- Separate TaskSpec, State, Context, Observation, Decision, Action, and Environment in code and prose.
- Treat retrieval, memory, planning, multi-agent, MCP, and A2A as extensions/composition/interoperability concepts, not as core synonyms for Agent.
- Record unresolved design decisions in `OPEN_QUESTIONS.md`.
- Record work performed and tests in `BUILD_LOG.md`.

## Execution

Start with Phase 0 in `OPENCODE_TASKS.md`, then proceed sequentially. Do not generate all chapters in one undifferentiated pass. Finish each module's chapter, lab, tests, exercises, quiz, trace, and acceptance checks before marking it complete.
