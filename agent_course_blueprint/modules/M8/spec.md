# M8 Spec — Planning, Workflows & Human Control

## Build
At least two control architectures over the same core runtime: reactive loop and plan/workflow variant; add approval/resume.

## Must Teach
- reactive vs explicit planning
- task decomposition
- plan representation
- plan-execute-replan
- deterministic state machine/workflow/graph
- when workflow beats agentic freedom
- human approval, correction, and escalation
- long-running/resumable tasks
- architecture selection criteria

## Lab Acceptance
- same benchmark task runs under two architectures
- traces reveal control differences
- human approval can pause and resume a side-effecting action
- replanning has an explicit trigger
