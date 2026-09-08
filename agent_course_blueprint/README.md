# Agent Engineering Course Blueprint — V2

This repository contains a complete, runnable Agent Engineering course with cumulative reference implementation, labs, evaluations, and a capstone project.

## Quick Start

```bash
# 1. Install dependencies
cd reference_agent
pip install -e ".[dev]"

# 2. Run the full test suite (272 tests, no credentials required)
cd ..
python -m pytest

# 3. Try the capstone CLI
python projects/cli.py --help
python projects/cli.py list-files projects/fixtures/simple_python
python projects/cli.py analyze projects/fixtures/simple_python --mock
```

## Course Structure

| Module | Theme | Lab | Tests |
|--------|-------|-----|-------|
| M0 | Agent System Mental Model | Runtime trace walkthrough | ✓ |
| M1 | Model Runtime & Structured Interaction | Model adapter implementation | ✓ |
| M2 | Tools & Action Interfaces | Tool registry/executor | ✓ |
| M3 | State, Control Loop & Termination | **Milestone 1:** Local Tool Agent | ✓ |
| M4 | Evaluation, Tracing & Failure Analysis | Trace + eval harness | ✓ |
| M5 | Context Engineering & Working State | Context builder | ✓ |
| M6 | Retrieval, Grounding & Evidence | Retrieval/evidence layer | ✓ |
| M7 | Memory & Persistence | **Milestone 2:** Measured Grounded Agent | ✓ |
| M8 | Planning, Workflows & Human Control | **Milestone 3:** Stateful Planning Agent | ✓ |
| M9 | Delegation, Multi-Agent & Protocols | **Milestone 4:** Composed Agent System | ✓ |
| M10 | Safety, Reliability & Resource Control | Guardrails/budgets/reliability | ✓ |
| M11 | Production Delivery & Operations | Deployable service + ops | ✓ |
| Capstone | Project Understanding Agent | Complete production-style system | 8 tests |

**Total: 272 tests passing** across all modules.

## Key Concepts

The course uses a canonical ontology (see `docs/ONTOLOGY.md`):

> An **Agent** is a stateful runtime controller that pursues a TaskSpec by repeatedly observing its environment, constructing decision context, selecting actions through a policy (often model-backed), updating state, and terminating according to explicit success, failure, or budget conditions.

**Important non-equivalences:**
- LLM ≠ Agent
- Prompt ≠ Context
- Chat history ≠ State
- Tool calling ≠ Agent
- RAG ≠ Agent
- Workflow ≠ Agent

## Repository Layout

```
agent_course_blueprint/
├── reference_agent/          # Cumulative reference implementation
│   ├── src/agent_course/
│   │   ├── core/            # TaskSpec, Observation, State, Decision, Transition
│   │   ├── llm/             # Model adapters (OpenAI, Anthropic, Fake)
│   │   ├── tools/           # Tool registry and executor
│   │   ├── runtime/         # Agent control loop
│   │   ├── evals/           # Evaluation harness
│   │   ├── context/         # Context builder
│   │   ├── retrieval/       # Retrieval and evidence grounding
│   │   ├── memory/          # Checkpoint and memory policy
│   │   ├── planning/        # Planning and workflows
│   │   ├── composition/     # Multi-agent composition
│   │   ├── safety/          # Permissions, guardrails, budgets
│   │   └── api/             # CLI, service, monitoring
│   └── tests/               # 264 tests
├── modules/                  # Course content
│   └── M*/                  # Each module has:
│       ├── chapter.md       # Lecture content
│       ├── lab/             # Hands-on exercises
│       ├── exercises.md     # Practice problems
│       ├── quiz.md          # Assessment questions
│       └── quiz_answers.md  # Answer key
├── projects/                 # Capstone project
│   ├── src/                 # Project Understanding Agent
│   ├── fixtures/            # 5 test repositories
│   ├── cli.py               # CLI entry point
│   └── tests/               # 8 tests
├── docs/                     # Specification documents
│   ├── ONTOLOGY.md          # Canonical conceptual model
│   ├── FAILURE_MODEL.md     # Debugging taxonomy
│   ├── ARCHITECTURE.md      # Runtime architecture
│   └── PROTOCOLS.md         # MCP/A2A placement
└── BUILD_LOG.md             # Development history
```

## Running Examples

### Basic Agent (M3)
```python
from agent_course.core import TaskSpec
from agent_course.llm import FakeModel, ModelResponse
from agent_course.tools import create_builtin_tools
from agent_course.runtime import Agent

model = FakeModel(responses=[
    ModelResponse(content="", tool_calls=[{"id": "1", "name": "list_files", "arguments": {"path": "."}}]),
    ModelResponse(content="Found 5 files."),
])

agent = Agent(model=model, tools=create_builtin_tools())
task = TaskSpec(goal="List files in current directory")
result = agent.run(task)
print(result.output)
```

### Capstone CLI
```bash
# Analyze a project
python projects/cli.py analyze projects/fixtures/web_app --mock

# List files
python projects/cli.py list-files projects/fixtures/simple_python

# Show structure
python projects/cli.py structure projects/fixtures/microservice
```

## Testing

All tests run offline with no API credentials required:

```bash
# Full test suite
python -m pytest

# Specific module
python -m pytest reference_agent/tests/test_runtime.py

# Capstone tests
python -m pytest projects/tests/
```

## Important Files

- `COURSE_CONFIG.yaml` — language and implementation defaults
- `docs/ONTOLOGY.md` — frozen Agent conceptual model
- `COURSE_BLUEPRINT.md` — course-level design
- `CURRICULUM_MAP.md` — M0–M11 topic map
- `docs/ARCHITECTURE.md` — canonical runtime architecture
- `docs/FAILURE_MODEL.md` — debugging/evaluation taxonomy
- `docs/REFERENCE_IMPLEMENTATION.md` — cumulative code evolution
- `docs/PROTOCOLS.md` — MCP/A2A placement
- `OPENCODE_TASKS.md` — phased build plan
- `modules/M*/spec.md` — module acceptance specs
- `projects/CAPSTONE.md` — final project

## Core Principle

Do not teach Agent engineering as framework memorization. Make the runtime state transition visible first; frameworks and protocols are later implementation/composition choices.

## License

Educational use. See individual module files for details.
