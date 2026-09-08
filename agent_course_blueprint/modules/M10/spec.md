# M10 Spec — Safety, Reliability & Resource Control

## Build
Permission layer, guardrails, budget manager, retry/timeout policy, sandbox abstraction or mock boundary.

## Must Teach
- threat modeling for agent actions
- least privilege
- read/write/execute permission tiers
- sandbox boundaries
- prompt injection / indirect injection
- untrusted tool/data boundaries
- input/output/tool guardrails
- irreversible side effects and approvals
- timeout/retry/backoff/circuit breaker
- rate limits
- token/step/time/cost budgets
- model routing/fallback

## Lab Acceptance
- unsafe side effect is blocked in test
- budget exhaustion terminates cleanly
- retryable vs non-retryable errors are distinguished
- guardrail decisions appear in traces
