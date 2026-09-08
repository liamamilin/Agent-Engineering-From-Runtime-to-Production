# OpenCode Execution Plan — V2

## Phase 0 — Freeze the Runtime and Scaffold

- [x] Read all mandatory architecture/spec files.
- [x] Create `BUILD_LOG.md` and `OPEN_QUESTIONS.md`.
- [x] Create `pyproject.toml` and `reference_agent/` skeleton.
- [x] Implement the core typed data objects with no external model dependency.
- [x] Add a deterministic fake policy/model for offline tests.
- [x] Add an initial trace schema.
- [x] Verify `pytest` passes with zero credentials.

Acceptance:
- TaskSpec, Observation, State, Decision, Transition and termination are represented explicitly.
- one deterministic fake run can be traced end-to-end.

## Phase 1 — Foundations and Minimal Agent (M0–M3)

- [x] Complete M0 artifacts.
- [x] Complete M1 model adapter lab.
- [x] Complete M2 tool registry/executor lab.
- [x] Complete M3 explicit loop/state/termination lab.
- [x] Complete Milestone 1.

Acceptance:
- a CLI Agent can receive a TaskSpec, choose a local tool, execute it, incorporate the result, update state, and terminate for an explicit reason.

## Phase 2 — Measurement and Grounding (M4–M6)

- [x] Complete M4 trace/eval harness.
- [x] Create a JSONL golden-task dataset.
- [x] Complete M5 ContextBuilder and budget policy.
- [x] Complete M6 retrieval/evidence layer.
- [x] Complete Milestone 2.

Acceptance:
- each run exposes step traces.
- evaluation separates task success, action correctness, groundedness, latency/cost proxies.
- important claims can reference evidence objects.

## Phase 3 — Persistence and Control Architecture (M7–M8)

- [x] Complete M7 checkpoint/memory policy.
- [x] Complete M8 planning/workflow/HITL patterns.
- [x] Complete Milestone 3.

Acceptance:
- run state can be saved/resumed.
- memory writes are policy controlled.
- a human approval checkpoint can interrupt and resume a run.
- at least two control architectures are compared on the same task.

## Phase 4 — Composition and Production (M9–M11)

- [x] Complete M9 composition and protocol material.
- [x] Implement one justified agent-as-tool or handoff example.
- [x] Add one small MCP adapter/example; keep it version-isolated.
- [x] Explain A2A-style interoperability; implementation optional unless dependencies are stable.
- [x] Complete M10 safety/reliability/resource controls.
- [x] Complete M11 API/ops/deployment material.
- [x] Complete Milestone 4.

Acceptance:
- multi-agent example is compared with a single-agent baseline.
- tool permissions and budget controls are enforced in code.
- service can be started with mock model mode.

## Phase 5 — Capstone

- [x] Implement Project Understanding Agent.
- [x] Add at least 5 repository fixtures.
- [x] Create structured Evidence and Claim models.
- [x] Track explored/unexplored areas.
- [x] Add coverage and hallucination-oriented evals.
- [x] Add trace examples and cost/latency summary.
- [x] Provide CLI and/or FastAPI entry point.

## Phase 6 — Editorial and Release Pass

- [x] Check terminology against `docs/ONTOLOGY.md`.
- [x] Check failures against `docs/FAILURE_MODEL.md`.
- [x] Remove framework-first explanations.
- [x] Remove duplicated prose.
- [x] Ensure every lab builds cumulatively.
- [x] Run full test suite.
- [x] Run eval suite.
- [x] Generate final course index and setup guide.
