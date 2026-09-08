# M1 Spec — Model Runtime & Structured Interaction

## Build
Provider-independent `ModelClient` plus deterministic `FakeModel`.

## Must Teach
- request/response lifecycle
- roles/instruction layers
- structured output and schema validation
- reasoning/sampling controls at a conceptual level
- streaming
- token/context limits
- timeout/retry/provider errors
- provider abstraction
- why Model is a runtime dependency, not the Agent itself

## Lab Acceptance
- fake model passes offline tests
- one real-provider adapter can be configured optionally
- structured output is parsed and validated
- failures are surfaced explicitly
