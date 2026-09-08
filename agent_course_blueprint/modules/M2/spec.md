# M2 Spec — Tools & Action Interfaces

## Build
Tool schema, registry, validator, dispatcher, executor, and typed result.

## Must Teach
- tools as environment interfaces
- tool schema and capability description
- model decision -> tool call -> validation -> execution -> result -> next observation
- argument validation
- side effects and idempotency
- permissions
- read vs write actions
- tool errors and retries
- untrusted tool descriptions

## Lab Acceptance
- at least three local tools
- invalid arguments fail before execution
- write/side-effect tool requires explicit permission flag or approval mock
- tool results become observations rather than being hidden
