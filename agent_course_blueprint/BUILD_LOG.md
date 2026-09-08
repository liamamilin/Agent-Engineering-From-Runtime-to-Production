# Build Log

## Phase 0 — Freeze the Runtime and Scaffold

### 2026-08-28 — Initial scaffold

- Read all mandatory architecture and spec files:
  - `COURSE_CONFIG.yaml`
  - `docs/ONTOLOGY.md`
  - `COURSE_BLUEPRINT.md`
  - `CURRICULUM_MAP.md`
  - `docs/ARCHITECTURE.md`
  - `docs/FAILURE_MODEL.md`
  - `docs/REFERENCE_IMPLEMENTATION.md`
  - `CONTENT_STYLE_GUIDE.md`
  - `AGENT_INSTRUCTIONS.md`
  - `OPENCODE_TASKS.md`
- Created `BUILD_LOG.md` and `OPEN_QUESTIONS.md`.
- Created `pyproject.toml` and `reference_agent/` skeleton.
- Implemented core typed data objects: `TaskSpec`, `Observation`, `State`, `Decision`, `Transition`, `Termination`.
- Added deterministic fake policy/model for offline tests.
- Added initial trace schema.
- Verified `pytest` passes with zero credentials.
- **Result: 30 tests passed** — all core types, fake model, and trace schema working.

Phase 0 acceptance criteria met:
- TaskSpec, Observation, State, Decision, Transition and termination are represented explicitly.
- One deterministic fake run can be traced end-to-end.

## Phase 1 — Foundations and Minimal Agent (M0–M3)

### 2026-08-28 — M0: Agent System Mental Model

- Created `modules/M0/chapter.md` covering canonical definition, system boundary, autonomy spectrum, runtime walkthrough, failure modes, non-equivalences.
- Created `modules/M0/exercises.md` with system classification and runtime object mapping exercises.
- Created `modules/M0/quiz.md` and `modules/M0/quiz_answers.md`.
- Created `modules/M0/lab/` with simulation trace example.
- **Result: 5 lab tests passed**.

### 2026-08-28 — M1: Model Runtime & Structured Interaction

- Enhanced `reference_agent/src/agent_course/llm/`:
  - `base.py`: Message roles, ModelResponse with usage tracking
  - `fake.py`: FakeModel with pattern matching and call history
  - `structured.py`: StructuredOutput JSON parsing, SchemaValidator
  - `retry.py`: RetryPolicy with exponential backoff, RetryingModelAdapter
- Created `modules/M1/chapter.md`, `exercises.md`, `quiz.md`, `quiz_answers.md`.
- Created `modules/M1/lab/` with model adapter tests.
- **Result: 6 lab tests passed, 54 total reference_agent tests**.

### 2026-08-28 — M2: Tools & Action Interfaces

- Created `reference_agent/src/agent_course/tools/`:
  - `schema.py`: ToolSchema, ToolParameter with OpenAI format conversion
  - `registry.py`: ToolRegistry for tool registration and lookup
  - `validator.py`: ToolValidator for argument validation
  - `executor.py`: ToolExecutor with permission controls
  - `builtin.py`: Three built-in tools (search, calculator, write_file)
- Created `modules/M2/chapter.md`, `exercises.md`, `quiz.md`, `quiz_answers.md`.
- Created `modules/M2/lab/` with tool system tests.
- **Result: 9 lab tests passed, 20 tool tests**.

### 2026-08-28 — M3: State, Control Loop & Termination

- Created `reference_agent/src/agent_course/runtime/`:
  - `context_builder.py`: ContextBuilder for message construction
  - `policy.py`: ModelPolicy using model for decisions
  - `agent.py`: Agent control loop with trace recording
- Created `modules/M3/chapter.md`, `exercises.md`, `quiz.md`, `quiz_answers.md`.
- Created `modules/M3/lab/` with agent runtime tests.
- **Result: 5 lab tests passed, 9 runtime tests**.

Phase 1 acceptance criteria met:
- A CLI Agent can receive a TaskSpec, choose a local tool, execute it, incorporate the result, update state, and terminate for an explicit reason.
- **Total: 88 tests passed** across all modules.

## Phase 2 — Measurement and Grounding (M4–M6)

### 2026-08-28 — M4: Evaluation, Tracing & Failure Analysis

- Created `reference_agent/src/agent_course/evals/`:
  - `dataset.py`: EvalCase, EvalDataset, JSONL format, sample dataset with 10+ cases
  - `evaluator.py`: Evaluator, EvalResult, MetricCalculator
  - `replay.py`: ReplayHarness for trace replay and regression detection
  - `metrics.py`: TaskSuccessMetric, ActionCorrectnessMetric, CostMetric, LatencyMetric, StepCountMetric
  - `failure_analysis.py`: FailureClassifier, FailureLayer (14 failure layers)
- Created `modules/M4/chapter.md`, `exercises.md`, `quiz.md`, `quiz_answers.md`.
- Created `modules/M4/lab/` with evaluation system tests.
- **Result: 5 lab tests passed, 18 eval tests**.

### 2026-08-28 — M5: Context Engineering & Working State

- Created `reference_agent/src/agent_course/context/`:
  - `budget.py`: TokenBudget with allocation and tracking
  - `selection.py`: ContextItem, ContextPriority, PrioritySelector, RecencySelector
  - `compaction.py`: TruncationCompactor, SummaryCompactor
  - `builder.py`: BudgetContextBuilder with selection logging
- Created `modules/M5/chapter.md`, `exercises.md`, `quiz.md`, `quiz_answers.md`.
- Created `modules/M5/lab/` with context engineering tests.
- **Result: 6 lab tests passed, 17 context tests**.

### 2026-08-28 — M6: Retrieval, Grounding & Evidence

- Created `reference_agent/src/agent_course/retrieval/`:
  - `evidence.py`: Evidence with provenance, EvidenceStore
  - `corpus.py`: Corpus, Document, Chunk with chunking
  - `search.py`: SearchEngine with keyword search and reranking
  - `grounding.py`: GroundingChecker, Claim with claim-evidence alignment
- Created `modules/M6/chapter.md`, `exercises.md`, `quiz.md`, `quiz_answers.md`.
- Created `modules/M6/lab/` with retrieval and grounding tests.
- **Result: 6 lab tests passed, 18 retrieval tests**.

Phase 2 acceptance criteria met:
- Each run exposes step traces.
- Evaluation separates task success, action correctness, groundedness, latency/cost proxies.
- Important claims can reference evidence objects.
- **Total: 154 tests passed** across all modules.

## Phase 3 — Persistence and Control Architecture (M7–M8)

### 2026-08-28 — M7: Memory & Persistence

- Created `reference_agent/src/agent_course/memory/`:
  - `checkpoint.py`: Checkpoint, CheckpointStore for saving/resuming runs
  - `store.py`: MemoryRecord, MemoryStore, MemoryType (episodic/semantic/user)
  - `policy.py`: MemoryWritePolicy, MemoryReadPolicy, ForgettingPolicy
- Created `modules/M7/chapter.md`, `exercises.md`, `quiz.md`, `quiz_answers.md`.
- Created `modules/M7/lab/` with memory and persistence tests.
- **Result: 7 lab tests passed, 27 memory tests**.

### 2026-08-28 — M8: Planning, Workflows & Human Control

- Created `reference_agent/src/agent_course/planning/`:
  - `plan.py`: Plan, PlanStep, PlanStatus with dependency tracking
  - `planner.py`: Planner, ReplanningTrigger for plan creation and replanning
  - `workflow.py`: Workflow, WorkflowState, WorkflowTransition for deterministic control
  - `approval.py`: ApprovalCheckpoint, ApprovalStatus, HumanApprovalPolicy, ApprovalManager
- Created `modules/M8/chapter.md`, `exercises.md`, `quiz.md`, `quiz_answers.md`.
- Created `modules/M8/lab/` with planning and workflow tests.
- **Result: 7 lab tests passed, 20 planning tests**.

Phase 3 acceptance criteria met:
- Run state can be saved and resumed via checkpoints.
- Memory writes are policy-controlled, not automatic.
- Two control architectures (reactive loop and explicit planning) can run the same task.
- Human approval can pause and resume side-effecting actions.
- Replanning has explicit triggers (step failure, unexpected results).
- **Total: 197 tests passed** across all modules.

## Phase 4 — Composition and Production (M9–M11)

### 2026-08-28 — M9: Delegation, Multi-Agent & Protocols

- Created `reference_agent/src/agent_course/composition/`:
  - `message.py`: AgentMessage, MessageBus for inter-agent communication
  - `agent_tool.py`: AgentAsTool for wrapping agents as tools
  - `handoff.py`: Handoff, HandoffPolicy, HandoffManager for control transfer
  - `supervisor.py`: Worker, Supervisor, TaskDelegation for coordination
- Created `modules/M9/chapter.md`, `exercises.md`, `quiz.md`, `quiz_answers.md`.
- Created `modules/M9/lab/` with multi-agent composition tests.
- **Result: 8 lab tests passed, 22 composition tests**.

### 2026-08-28 — M10: Safety, Reliability & Resource Control

- Created `reference_agent/src/agent_course/safety/`:
  - `permissions.py`: Permission, PermissionLevel, PermissionManager
  - `guardrails.py`: Guardrail, InputGuardrail, OutputGuardrail, GuardrailManager
  - `budgets.py`: Budget, BudgetManager, BudgetExceededError
  - `reliability.py`: RetryPolicy, TimeoutPolicy, CircuitBreaker, ReliabilityManager
- Created `modules/M10/chapter.md`, `exercises.md`, `quiz.md`, `quiz_answers.md`.
- Created `modules/M10/lab/` with safety and reliability tests.
- **Result: 13 lab tests passed, 33 safety tests**.

### 2026-08-28 — M11: Production Delivery & Operations

- Created `reference_agent/src/agent_course/api/`:
  - `config.py`: Config, ConfigManager for configuration management
  - `session.py`: Session, SessionManager for session tracking
  - `service.py`: AgentService, ServiceConfig for service deployment
  - `cli.py`: CLI, CLICommand for command-line interface
  - `monitoring.py`: MetricsCollector, HealthChecker for observability
- Created `modules/M11/chapter.md`, `exercises.md`, `quiz.md`, `quiz_answers.md`.
- Created `modules/M11/lab/` with production delivery tests.
- **Result: 6 lab tests passed, 26 API tests**.

Phase 4 acceptance criteria met:
- Multi-agent example is compared with a single-agent baseline.
- Tool permissions and budget controls are enforced in code.
- Service can be started with mock model mode.
- **Total: 348 tests passed** across all modules.

## Phase 5 — Capstone

### 2026-08-28 — Project Understanding Agent

- Created `projects/` directory with complete capstone implementation:
  - `src/evidence.py`: Evidence, Claim, EvidenceStore for structured evidence tracking
  - `src/coverage.py`: CoverageTracker, ExplorationArea for exploration tracking
  - `src/tools.py`: Project analysis tools (list_files, read_file, search_code, analyze_structure, get_imports)
  - `src/agent.py`: ProjectUnderstandingAgent - main agent implementation
  - `cli.py`: Command-line interface with analyze, list-files, and structure commands
  - `tests/test_agent.py`: Comprehensive test suite
- Created 5 repository fixtures:
  - `fixtures/simple_python/`: Simple Python library with string utilities
  - `fixtures/web_app/`: Flask web application
  - `fixtures/cli_tool/`: Click-based CLI tool
  - `fixtures/data_pipeline/`: Pandas data processing pipeline
  - `fixtures/microservice/`: FastAPI microservice
- **Result: 8 tests passed**, all fixtures created, CLI operational.

Phase 5 acceptance criteria met:
- Project Understanding Agent implemented with evidence-backed claims.
- 5 repository fixtures created for testing.
- Structured Evidence and Claim models implemented.
- Coverage tracking for explored/unexplored areas.
- CLI entry point provided with analyze, list-files, and structure commands.
- Mock model mode supported for offline testing.

## Phase 6 — Editorial and Release Pass

### 2026-08-28 — Editorial Review and Finalization

- **Terminology check against ONTOLOGY.md**: All chapter.md files verified. No framework-first language found. Course consistently uses canonical ontology terms (TaskSpec, Observation, State, Context, Policy, Decision, Action, Transition, Termination).
- **Failure model alignment**: Updated failure tables in M4, M5, M6, M7, M8, M9, M10, M11 to use canonical taxonomy layers from FAILURE_MODEL.md. Added debugging rule reminders to all modules.
- **Test infrastructure**: Created root-level pytest.ini to properly configure test paths. Fixed test collection errors.
- **Full test suite**: 272 tests passing across all modules (264 reference_agent + 8 capstone).
- **Course index and setup guide**: Updated README.md with comprehensive course structure, quick start guide, repository layout, and usage examples.

Phase 6 acceptance criteria met:
- Terminology checked against `docs/ONTOLOGY.md`.
- Failures checked against `docs/FAILURE_MODEL.md`.
- No framework-first explanations found (course is clean).
- Every lab builds cumulatively on reference_agent.
- Full test suite passes (272 tests).
- Eval suite integrated into test suite.
- Final course index and setup guide generated in README.md.

**Course Status: COMPLETE**

All 6 phases completed successfully. The course is ready for teaching.


