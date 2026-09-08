# M11 Spec — Production Delivery & Operations

## Build
Deployable mock-mode CLI/FastAPI service, config layer, session persistence, monitoring hooks, version metadata.

## Must Teach
- service boundary and API contract
- sessions and persistence
- concurrency and cancellation
- config/secrets
- deployment patterns
- prompt/tool/model versioning
- rollout and rollback
- monitoring and alerting concepts
- incident debugging with trace replay
- production benchmarks
- cost/latency/quality tradeoffs

## Lab Acceptance
- service starts without external credentials in mock mode
- request has run ID and version metadata
- concurrent-run state is isolated
- trace/replay path is documented
