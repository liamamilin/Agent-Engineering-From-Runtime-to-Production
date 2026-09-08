# Agent Failure Model

The course uses one stable failure taxonomy so debugging does not collapse into "the model was bad".

| Layer | Failure Class | Example |
|---|---|---|
| Task | specification failure | success criterion is undefined |
| Observation | perception/input failure | tool output is incomplete or misparsed |
| Context | context construction failure | relevant evidence omitted; injection included |
| Policy | decision failure | wrong next action selected |
| Action | tool/action failure | invalid arguments; permission denied; side effect failed |
| Transition | state update failure | successful result not recorded |
| Control | orchestration failure | loop repeats, deadlocks, or stops too early |
| Knowledge | grounding failure | unsupported claim or poor retrieval |
| Memory | persistence failure | stale/incorrect memory reused |
| Composition | delegation failure | wrong worker, duplicated work, context leakage |
| Safety | boundary failure | unsafe tool execution or data disclosure |
| Reliability | infrastructure failure | timeout, rate limit, provider outage |
| Resource | budget failure | excessive tokens, steps, latency, or cost |
| Evaluation | measurement failure | metric rewards the wrong behavior |

## Debugging Rule

Every lab should map observed failures to one or more layers before proposing a fix.

## Evaluation Rule

Do not rely on one final-answer score. Prefer layered checks:

1. Did the task finish?
2. Were decisions valid?
3. Were actions correct?
4. Was evidence sufficient?
5. Was state updated correctly?
6. Did the system respect budgets and safety constraints?
7. Was the final output correct and useful?
