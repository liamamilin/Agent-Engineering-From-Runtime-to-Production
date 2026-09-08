from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterator


@dataclass
class EvalCase:
    """A single evaluation case (golden task)."""

    id: str
    task_goal: str
    success_criteria: list[str]
    expected_output: str | None = None
    expected_tool_calls: list[str] = field(default_factory=list)
    max_steps: int = 10
    constraints: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvalCase:
        return cls(**data)


@dataclass
class EvalDataset:
    """A collection of evaluation cases."""

    name: str
    cases: list[EvalCase] = field(default_factory=list)
    version: str = "1.0"
    description: str = ""

    def add_case(self, case: EvalCase) -> None:
        self.cases.append(case)

    def get_case(self, case_id: str) -> EvalCase | None:
        for case in self.cases:
            if case.id == case_id:
                return case
        return None

    def __iter__(self) -> Iterator[EvalCase]:
        return iter(self.cases)

    def __len__(self) -> int:
        return len(self.cases)


def save_dataset(dataset: EvalDataset, path: str | Path) -> None:
    """Save dataset to JSONL format."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        # First line is metadata
        metadata = {"name": dataset.name, "version": dataset.version, "description": dataset.description}
        f.write(json.dumps(metadata, ensure_ascii=False) + "\n")
        # Remaining lines are cases
        for case in dataset.cases:
            f.write(json.dumps(case.to_dict(), ensure_ascii=False) + "\n")


def load_dataset(path: str | Path) -> EvalDataset:
    """Load dataset from JSONL format."""
    path = Path(path)

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        raise ValueError(f"Empty dataset file: {path}")

    # First line is metadata
    metadata = json.loads(lines[0])
    dataset = EvalDataset(
        name=metadata.get("name", "unnamed"),
        version=metadata.get("version", "1.0"),
        description=metadata.get("description", ""),
    )

    # Remaining lines are cases
    for line in lines[1:]:
        if line.strip():
            case_data = json.loads(line)
            dataset.add_case(EvalCase.from_dict(case_data))

    return dataset


def create_sample_dataset() -> EvalDataset:
    """Create a sample evaluation dataset for testing."""
    dataset = EvalDataset(
        name="sample_agent_eval",
        version="1.0",
        description="Sample evaluation cases for agent testing",
    )

    # Case 1: Simple calculation
    dataset.add_case(EvalCase(
        id="calc_001",
        task_goal="Calculate 15 * 7",
        success_criteria=["Correct result: 105"],
        expected_output="105",
        expected_tool_calls=["calculator"],
        max_steps=5,
    ))

    # Case 2: Search and answer
    dataset.add_case(EvalCase(
        id="search_001",
        task_goal="What is the capital of France?",
        success_criteria=["Answer mentions Paris"],
        expected_output="Paris",
        expected_tool_calls=["search"],
        max_steps=5,
    ))

    # Case 3: Multi-step task
    dataset.add_case(EvalCase(
        id="multi_001",
        task_goal="Search for Python, then calculate the length of 'Python' times 10",
        success_criteria=["Search performed", "Calculation result: 60"],
        expected_tool_calls=["search", "calculator"],
        max_steps=10,
    ))

    # Case 4: Direct answer (no tools needed)
    dataset.add_case(EvalCase(
        id="direct_001",
        task_goal="Say hello",
        success_criteria=["Response contains greeting"],
        expected_output="Hello",
        expected_tool_calls=[],
        max_steps=3,
    ))

    # Case 5: File write with permission
    dataset.add_case(EvalCase(
        id="write_001",
        task_goal="Write 'test content' to /tmp/test.txt",
        success_criteria=["File written successfully"],
        expected_tool_calls=["write_file"],
        max_steps=5,
        constraints=["Requires permission"],
    ))

    # Case 6: Calculator with complex expression
    dataset.add_case(EvalCase(
        id="calc_002",
        task_goal="Calculate (10 + 5) * 2 - 3",
        success_criteria=["Correct result: 27"],
        expected_output="27",
        expected_tool_calls=["calculator"],
        max_steps=5,
    ))

    # Case 7: Multiple calculations
    dataset.add_case(EvalCase(
        id="calc_003",
        task_goal="Calculate 2+2, then 3*3, then add the results",
        success_criteria=["Results: 4, 9, 13"],
        expected_tool_calls=["calculator", "calculator", "calculator"],
        max_steps=10,
    ))

    # Case 8: Search with specific query
    dataset.add_case(EvalCase(
        id="search_002",
        task_goal="Search for machine learning tutorials",
        success_criteria=["Search performed with correct query"],
        expected_tool_calls=["search"],
        max_steps=5,
    ))

    # Case 9: Fallback test (tool fails)
    dataset.add_case(EvalCase(
        id="fallback_001",
        task_goal="Use nonexistent_tool to get info",
        success_criteria=["Graceful failure or fallback"],
        expected_tool_calls=["nonexistent_tool"],
        max_steps=5,
    ))

    # Case 10: Max steps test
    dataset.add_case(EvalCase(
        id="maxsteps_001",
        task_goal="Keep searching forever",
        success_criteria=["Terminates at max_steps"],
        expected_tool_calls=["search"],
        max_steps=3,
    ))

    return dataset
