# Curriculum Map — V2

The course moves from a minimal single-agent runtime to grounded, stateful, composed, production systems.

## Stage 0 — Foundations

### M0 — Agent System Mental Model
- LLM call vs workflow vs agent
- system boundary
- TaskSpec / Observation / State / Context / Policy / Action / Environment
- autonomy spectrum
- deterministic vs probabilistic components
- trace one complete run

### M1 — Model Runtime & Structured Interaction
- request/response lifecycle
- messages and instruction layers
- structured outputs
- reasoning / sampling controls
- streaming
- provider adapters
- errors, retries, timeouts

## Stage 1 — Minimal Agent Runtime

### M2 — Tools & Action Interfaces
- tool schemas
- selection and arguments
- dispatch and execution
- validation
- tool result injection
- side effects, idempotency, permissions

### M3 — State, Control Loop & Termination
- TaskSpec and success criteria
- runtime State
- observation / decision / action
- explicit loop
- transition functions
- stop conditions and budgets
- fallback / retry

**Milestone 1:** Local Tool Agent

## Stage 2 — Measure Before Adding Complexity

### M4 — Evaluation, Tracing & Failure Analysis
- traces and spans
- failure taxonomy
- golden tasks
- deterministic checks
- model-based judges and limitations
- task success / action correctness / latency / cost
- replay and regression tests

From this point forward, every new capability must add tests and eval cases.

## Stage 3 — Information & Knowledge

### M5 — Context Engineering & Working State
- context composition
- instruction/task/state/tool-data separation
- context budgets
- selection and prioritization
- compaction / summarization
- prompt injection boundaries
- context inspection

### M6 — Retrieval, Grounding & Evidence
- retrieval as information acquisition
- keyword / semantic search
- chunking/indexing/reranking
- query transformation
- evidence objects
- provenance/citations
- claim-evidence alignment
- retrieval evaluation

**Milestone 2:** Measured Grounded Agent

### M7 — Memory & Persistence
- transient state vs session state vs durable memory
- checkpoints
- episodic / semantic / user memory
- memory write policy
- retrieval policy
- forgetting / invalidation
- privacy boundaries

## Stage 4 — Control Architecture

### M8 — Planning, Workflows & Human Control
- reactive loop vs explicit plan
- task decomposition
- plan-execute-replan
- deterministic workflows / state machines / graphs
- human approval and intervention
- resumable/long-running tasks
- architecture selection rules

**Milestone 3:** Stateful Planning Agent

## Stage 5 — Composition & Interoperability

### M9 — Delegation, Multi-Agent & Protocols
- composition before multi-agent
- agent-as-tool
- handoffs
- supervisor/worker
- planner/executor/reviewer
- shared vs isolated context
- MCP as capability/context integration
- A2A-style agent interoperability
- compare against a single-agent baseline

**Milestone 4:** Composed Agent System

## Stage 6 — Trustworthy Production Systems

### M10 — Safety, Reliability & Resource Control
- threat model
- tool permissions
- sandbox boundaries
- prompt injection and untrusted content
- input/output/tool guardrails
- retries / timeouts / circuit breakers
- rate limits
- cost/token/step budgets
- model routing and fallback

### M11 — Production Delivery & Operations
- CLI/API/service boundaries
- sessions and persistence
- concurrency
- configuration and secrets
- deployment
- prompt/tool/model versioning
- rollout / rollback
- monitoring and incident analysis
- trace replay
- production benchmarks

## Capstone — Project Understanding Agent

The learner receives an unfamiliar software repository and builds an evidence-backed Agent that explores it, tracks coverage, forms and revises a plan, gathers evidence, produces claims with provenance, evaluates itself on fixtures, and exposes a CLI or API.
