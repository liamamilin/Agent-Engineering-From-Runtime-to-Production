# M3 Spec — State, Control Loop & Termination

## Build
Explicit runtime loop using TaskSpec, State, Observation, Decision, Transition and Termination.

## Must Teach
- task goals and success criteria
- state vs messages
- observe -> context -> decide -> validate/act -> transition -> terminate
- max steps, cost/time/token budgets
- final/fail/ask-user/tool decisions
- retries/fallbacks
- deterministic controller around probabilistic policy
- termination reason as a first-class output

## Lab Acceptance
- one full tool-using run executes offline with FakeModel
- trace shows each state transition
- max-step termination is tested
- success termination is tested
- failure termination is tested
