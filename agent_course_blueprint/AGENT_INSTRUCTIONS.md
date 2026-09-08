# Instructions for OpenCode / Coding Agent — V2

You are implementing the first complete draft of an Agent Engineering course.

## Instruction Priority

1. `docs/ONTOLOGY.md`
2. `COURSE_BLUEPRINT.md`
3. `CURRICULUM_MAP.md`
4. `docs/ARCHITECTURE.md`
5. `docs/FAILURE_MODEL.md`
6. `CONTENT_STYLE_GUIDE.md`
7. module `spec.md`
8. templates

## Required Deliverables Per Module

1. `chapter.md`
2. `lab/README.md`
3. `lab/src/` runnable code
4. `lab/tests/`
5. `exercises.md`
6. `quiz.md`
7. `quiz_answers.md`
8. at least one example trace
9. after M4: eval additions/changes

## Reference Runtime

Create and evolve `reference_agent/` as specified in `docs/REFERENCE_IMPLEMENTATION.md`.

Do not replace the explicit runtime with LangChain/LangGraph/Agents SDK/etc. Framework comparisons or adapters may be added after the mechanism is implemented plainly.

## Technical Rules

- Python 3.11+
- use typed interfaces where they clarify boundaries
- all model/network interactions mockable
- tests run with no credentials
- no hidden global state
- no hard-coded keys
- validate tool arguments before side effects
- expose termination reasons
- expose run/step IDs in traces

## Writing Rules

Use the language and terminology policy in `COURSE_CONFIG.yaml`.

For each concept:
1. define it
2. explain why it exists
3. place it in the system boundary
4. show the runtime path
5. implement the minimum mechanism
6. show a trace
7. show failure modes
8. show how to evaluate it
9. derive engineering rules

## Completion Definition

A module is complete only when prose, code, tests, traces, exercises, quizzes and acceptance criteria agree with each other.

## Work Logging

Maintain:
- `BUILD_LOG.md`
- `OPEN_QUESTIONS.md`

Never make a major ontology or curriculum change without recording it as a proposal.
