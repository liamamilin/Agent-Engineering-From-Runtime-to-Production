# Evaluation Rubric

## Per-Module Lab Rubric — 100 points

| Dimension | Weight | Criteria |
|---|---:|---|
| Correctness | 30 | Required behavior works |
| Mechanism Understanding | 20 | Implementation exposes the module's core mechanism |
| Reliability | 15 | Handles expected errors / edge cases |
| Test Quality | 15 | Useful automated tests exist |
| Observability | 10 | Important state / failures are inspectable |
| Code Quality | 10 | Clear separation of concerns and readable structure |

## Capstone Rubric — 100 points

| Dimension | Weight |
|---|---:|
| Task Success | 20 |
| Architecture Quality | 15 |
| Tool Design | 10 |
| Context / State Design | 10 |
| Retrieval / Grounding | 10 |
| Evaluation Quality | 15 |
| Reliability / Safety | 10 |
| Cost / Latency Awareness | 5 |
| Documentation | 5 |

## Required Evaluation Metrics

At minimum, capstone evaluation must measure:

- success rate
- invalid tool call rate
- tool execution failure rate
- final answer/schema validity
- grounded/evidence-supported claim rate when applicable
- average model calls per task
- average tool calls per task
- latency
- estimated cost

## Failure Taxonomy

All evaluation failures should be classified into one primary category:

1. Input misunderstanding
2. Context omission / pollution
3. Planning / policy error
4. Tool selection error
5. Tool argument error
6. Tool execution error
7. State / memory error
8. Retrieval error
9. Final synthesis error
10. Infrastructure / provider error

