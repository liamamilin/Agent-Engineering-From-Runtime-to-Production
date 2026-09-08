# Capstone — Project Understanding Agent (V2)

## Goal

Build an Agent that can inspect an unfamiliar software repository and produce a structured, evidence-backed engineering report while making its runtime decisions, evidence, coverage, costs, and limitations observable.

## TaskSpec

Input:
- repository path
- analysis goal / optional user question
- success criteria
- step/time/cost budget
- allowed tool permissions

Example success criteria:
- identify project purpose and major capabilities
- explain main architecture and runtime workflows
- support major claims with evidence
- identify important unknowns instead of hallucinating
- reach configured repository coverage threshold or justify early termination

## Required Outputs

1. Project overview
2. File/package structure
3. Main capabilities
4. Architecture
5. Important runtime workflows
6. Configuration and environment
7. External tools/services/integrations
8. Risks and unknowns
9. Evidence references
10. Recommendations
11. Coverage summary
12. Run summary: steps, termination reason, latency/cost proxy

## Required Tools

At minimum:
- file tree/listing
- file reader
- text/code search
- dependency/config parser

Optional:
- test runner
- symbol parser
- git history reader
- shell tool behind explicit permission/sandbox boundary

## Required Runtime Behaviors

- maintain explicit `RepoAnalysisState`
- form and revise an exploration plan or use a justified deterministic workflow
- gather evidence before making major claims
- track explored/unexplored areas
- avoid duplicate reads/searches without explicit reason
- distinguish Evidence, Claim, Inference, Unknown, Recommendation
- attach provenance to important claims
- stop when success/coverage is sufficient or a budget/failure condition is reached
- expose a termination reason

## Suggested Types

```python
class Evidence:
    id: str
    source: str
    locator: str
    excerpt_or_summary: str
    confidence: float | None

class Claim:
    id: str
    statement: str
    evidence_ids: list[str]
    kind: str  # evidence-backed | inference | unknown
    confidence: float | None

class RepoAnalysisState:
    goal: str
    discovered_files: list[str]
    selected_files: list[str]
    evidence: list[Evidence]
    claims: list[Claim]
    open_questions: list[str]
    explored_areas: set[str]
    unexplored_areas: set[str]
    visited_operations: set[str]
    step_count: int
    budget_remaining: float | None
```

## Baseline Requirement

Implement a **single-agent baseline first**.

If a multi-agent/composed variant is added, compare it against the baseline on the same fixtures. Multi-agent is only justified if it produces a measurable advantage such as better coverage/quality or operational modularity worth its additional cost/latency/complexity.

## Evaluation Dataset

Create at least 5 small repository fixtures with known properties.

Measure:
- capability recall
- architecture claim correctness
- evidence coverage
- unsupported/hallucinated claim rate
- unknown calibration
- duplicated tool work
- repository coverage
- average steps
- termination correctness
- latency proxy
- token/cost proxy

## Safety Requirements

- read-only tools should be the default
- write/shell execution must require a separate permission boundary
- repository content is untrusted data and must not be treated as system instructions
- secrets should not be included in model context or final output

## Final Deliverable

- CLI and/or FastAPI endpoint
- Markdown and JSON report formats
- tests
- evaluation script
- example traces
- at least 5 fixtures
- README with architecture and limitations
- baseline comparison if composition/multi-agent is used
