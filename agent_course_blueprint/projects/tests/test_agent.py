"""Tests for Project Understanding Agent"""

import pytest
import sys
from pathlib import Path

# Add projects/src to path
projects_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(projects_src))

from evidence import Evidence, Claim, EvidenceStore
from coverage import CoverageTracker, ExplorationArea
from agent import ProjectUnderstandingAgent
from agent_course.llm import FakeModel, ModelResponse


@pytest.fixture
def simple_python_path():
    """Path to simple_python fixture"""
    return Path(__file__).parent.parent / "fixtures" / "simple_python"


@pytest.fixture
def fake_model():
    """Create a fake model for testing"""
    return FakeModel(responses=[
        ModelResponse(content="I'll analyze the project structure"),
        ModelResponse(content="The project is a Python library"),
    ])


def test_evidence_creation():
    """Test creating evidence"""
    evidence = Evidence(
        id="test-1",
        source="test.py",
        content="def test_function(): pass",
    )
    assert evidence.id == "test-1"
    assert evidence.source == "test.py"


def test_claim_creation():
    """Test creating a claim"""
    claim = Claim(
        id="claim-1",
        statement="This is a Python project",
        confidence=0.9,
        evidence_ids=["evidence-1"],
        category="structure",
    )
    assert claim.id == "claim-1"
    assert claim.confidence == 0.9
    assert claim.is_supported()


def test_evidence_store():
    """Test evidence store operations"""
    store = EvidenceStore()
    
    # Add evidence
    evidence = Evidence(id="e1", source="test.py", content="test")
    store.add_evidence(evidence)
    
    # Add claim
    claim = Claim(
        id="c1",
        statement="Test claim",
        confidence=0.8,
        evidence_ids=["e1"],
    )
    store.add_claim(claim)
    
    # Get summary
    summary = store.get_summary()
    assert summary["total_evidence"] == 1
    assert summary["total_claims"] == 1
    assert summary["supported_claims"] == 1


def test_coverage_tracker():
    """Test coverage tracker"""
    tracker = CoverageTracker()
    tracker.initialize_default_areas()
    
    # Check initial state
    assert len(tracker.areas) == 6
    assert tracker.get_coverage_percentage() == 0.0
    
    # Mark file as explored
    tracker.mark_file_explored("test.py", "structure")
    assert "test.py" in tracker.explored_files
    
    # Check coverage
    tracker.total_files = 10
    assert tracker.get_coverage_percentage() == 0.1


def test_project_agent_initialization(fake_model, simple_python_path):
    """Test project agent initialization"""
    agent = ProjectUnderstandingAgent(fake_model, str(simple_python_path))
    
    assert agent.project_path == simple_python_path
    assert len(agent.coverage_tracker.areas) == 6


def test_project_agent_tools(fake_model, simple_python_path):
    """Test that tools are registered"""
    agent = ProjectUnderstandingAgent(fake_model, str(simple_python_path))
    
    # Check that tools are registered
    tools = agent.agent._tools
    assert "list_files" in tools
    assert "read_file" in tools
    assert "search_code" in tools
    assert "analyze_structure" in tools


def test_project_agent_analysis(fake_model, simple_python_path):
    """Test project analysis"""
    agent = ProjectUnderstandingAgent(fake_model, str(simple_python_path))
    
    result = agent.analyze(goal="Understand the project structure")
    
    assert "success" in result
    assert "evidence_summary" in result
    assert "coverage_summary" in result
    assert "claims" in result


def test_project_agent_report(fake_model, simple_python_path):
    """Test getting analysis report"""
    agent = ProjectUnderstandingAgent(fake_model, str(simple_python_path))
    
    # Run analysis first
    agent.analyze(goal="Understand the project")
    
    # Get report
    report = agent.get_report()
    
    assert "project_path" in report
    assert "evidence_summary" in report
    assert "coverage_summary" in report
    assert "areas" in report
