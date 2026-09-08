# M4 Spec — Evaluation, Tracing & Failure Analysis

## Build
Trace schema, JSONL eval dataset, deterministic evaluator, replay harness, metric summary.

## Must Teach
- why evaluation comes before advanced capabilities
- run/step spans
- golden tasks
- layered evaluation
- task success vs action correctness vs output correctness
- cost/latency/step metrics
- LLM-as-judge strengths and limitations
- replay and regression
- failure taxonomy from `docs/FAILURE_MODEL.md`

## Lab Acceptance
- at least 10 small eval cases
- trace can reconstruct decisions/actions/state changes
- deterministic metrics run offline
- failures are assigned to layers
