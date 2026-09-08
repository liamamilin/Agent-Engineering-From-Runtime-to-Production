"""Project Understanding Agent - Main Implementation"""

from typing import Any, Optional
from pathlib import Path
import uuid

from agent_course.core import TaskSpec, Observation, AgentState, Decision
from agent_course.runtime import Agent
from agent_course.llm import ModelAdapter
from agent_course.tools import ToolRegistry, ToolSchema, ToolParameter, ParameterType

from evidence import Evidence, Claim, EvidenceStore
from coverage import CoverageTracker, ExplorationArea
from tools import list_files, read_file, search_code, analyze_structure, get_imports


class ProjectUnderstandingAgent:
    """Agent that understands and analyzes code repositories"""
    
    def __init__(self, model: ModelAdapter, project_path: str):
        """Initialize the project understanding agent"""
        self.model = model
        self.project_path = Path(project_path)
        self.evidence_store = EvidenceStore()
        self.coverage_tracker = CoverageTracker()
        self.coverage_tracker.initialize_default_areas()
        
        # Initialize underlying agent with tools
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create the underlying agent with project analysis tools"""
        # Create tool registry
        registry = ToolRegistry()
        
        # Register tools
        self._register_tools(registry)
        
        # Create agent
        agent = Agent(
            model=self.model,
            tools=registry,
            system_prompt=self._get_system_prompt(),
        )
        
        return agent
    
    def _register_tools(self, registry: ToolRegistry) -> None:
        """Register all project analysis tools"""
        # List files tool
        list_files_schema = ToolSchema(
            name="list_files",
            description="List files in the project matching a pattern",
            parameters=[
                ToolParameter(
                    name="pattern",
                    type=ParameterType.STRING,
                    description="Glob pattern to match files (default: **/*)",
                    required=False,
                ),
            ],
        )
        registry.register(
            list_files_schema,
            lambda pattern="**/*": list_files(str(self.project_path), pattern),
        )
        
        # Read file tool
        read_file_schema = ToolSchema(
            name="read_file",
            description="Read the contents of a file",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=ParameterType.STRING,
                    description="Path to the file relative to project root",
                    required=True,
                ),
            ],
        )
        registry.register(
            read_file_schema,
            lambda file_path: self._read_file_with_evidence(file_path),
        )
        
        # Search code tool
        search_code_schema = ToolSchema(
            name="search_code",
            description="Search for a pattern in code files",
            parameters=[
                ToolParameter(
                    name="pattern",
                    type=ParameterType.STRING,
                    description="Regex pattern to search for",
                    required=True,
                ),
                ToolParameter(
                    name="file_pattern",
                    type=ParameterType.STRING,
                    description="Glob pattern for files to search (default: **/*.py)",
                    required=False,
                ),
            ],
        )
        registry.register(
            search_code_schema,
            lambda pattern, file_pattern="**/*.py": search_code(
                str(self.project_path), pattern, file_pattern
            ),
        )
        
        # Analyze structure tool
        analyze_structure_schema = ToolSchema(
            name="analyze_structure",
            description="Analyze the project structure",
            parameters=[],
        )
        registry.register(
            analyze_structure_schema,
            lambda: self._analyze_structure_with_coverage(),
        )
        
        # Get imports tool
        get_imports_schema = ToolSchema(
            name="get_imports",
            description="Extract imports from a Python file",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=ParameterType.STRING,
                    description="Path to the Python file",
                    required=True,
                ),
            ],
        )
        registry.register(
            get_imports_schema,
            lambda file_path: self._get_imports_with_evidence(file_path),
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
        return f"""You are a Project Understanding Agent. Your task is to analyze and understand the code repository at {self.project_path}.

Your goals:
1. Explore the project structure and identify key components
2. Understand the architecture and design patterns
3. Identify dependencies and their purposes
4. Analyze the core logic and algorithms
5. Generate evidence-backed claims about the project

For each finding, you should:
- Collect evidence by reading relevant files
- Make claims with confidence levels
- Track what areas you've explored

Be thorough but efficient. Focus on understanding the project's purpose, architecture, and key components."""
    
    def _read_file_with_evidence(self, file_path: str) -> dict[str, Any]:
        """Read a file and record evidence"""
        result = read_file(str(self.project_path), file_path)
        
        if result["success"]:
            # Record evidence
            evidence = Evidence(
                id=str(uuid.uuid4()),
                source=file_path,
                content=result["content"][:500],  # Store first 500 chars
                metadata={"lines": result["lines"], "size": result["size"]},
            )
            self.evidence_store.add_evidence(evidence)
            
            # Update coverage
            area = self._determine_area(file_path)
            self.coverage_tracker.mark_file_explored(file_path, area)
        
        return result
    
    def _analyze_structure_with_coverage(self) -> dict[str, Any]:
        """Analyze structure and update coverage"""
        result = analyze_structure(str(self.project_path))
        
        if result["success"]:
            # Update total files
            self.coverage_tracker.total_files = result["total_files"]
            
            # Record evidence
            evidence = Evidence(
                id=str(uuid.uuid4()),
                source="structure_analysis",
                content=f"Project has {result['total_files']} files, "
                       f"{len(result['directories'])} directories",
                metadata=result,
            )
            self.evidence_store.add_evidence(evidence)
            
            # Mark structure area as explored
            self.coverage_tracker.mark_area_complete("structure")
        
        return result
    
    def _get_imports_with_evidence(self, file_path: str) -> dict[str, Any]:
        """Get imports and record evidence"""
        result = get_imports(str(self.project_path), file_path)
        
        if result["success"]:
            # Record evidence
            evidence = Evidence(
                id=str(uuid.uuid4()),
                source=f"{file_path}:imports",
                content=f"Imports: {', '.join(result['imports'][:10])}",
                metadata={"imports": result["imports"]},
            )
            self.evidence_store.add_evidence(evidence)
            
            # Update dependencies area
            self.coverage_tracker.mark_file_explored(file_path, "dependencies")
        
        return result
    
    def _determine_area(self, file_path: str) -> str:
        """Determine which exploration area a file belongs to"""
        file_path_lower = file_path.lower()
        
        if any(pattern in file_path_lower for pattern in ["test", "spec"]):
            return "testing"
        elif any(pattern in file_path_lower for pattern in ["config", "settings", "env"]):
            return "configuration"
        elif any(pattern in file_path_lower for pattern in ["main", "core", "app"]):
            return "core_logic"
        elif file_path.endswith((".py", ".js", ".ts", ".java", ".go", ".rs")):
            return "architecture"
        else:
            return "structure"
    
    def analyze(self, goal: str = "Understand the project structure and architecture") -> dict[str, Any]:
        """Run the analysis"""
        # Create task
        task = TaskSpec(
            goal=goal,
            success_criteria=[
                "Project structure analyzed",
                "Key components identified",
                "Architecture understood",
                "Claims backed by evidence",
            ],
            max_steps=20,
        )
        
        # Run agent
        result = self.agent.run(task)
        
        # Generate claims based on findings
        self._generate_claims()
        
        return {
            "success": result.success,
            "output": result.output,
            "evidence_summary": self.evidence_store.get_summary(),
            "coverage_summary": self.coverage_tracker.get_summary(),
            "claims": [c.to_dict() for c in self.evidence_store.claims.values()],
            "trace": {
                "run_id": result.trace.run_id,
                "task": result.trace.task,
                "steps": len(result.trace.steps),
            } if result.trace else None,
        }
    
    def _generate_claims(self) -> None:
        """Generate claims based on collected evidence"""
        # Generate structure claims
        structure_evidence = [e for e in self.evidence_store.evidence.values() 
                             if e.source == "structure_analysis"]
        if structure_evidence:
            claim = Claim(
                id=str(uuid.uuid4()),
                statement="Project structure has been analyzed",
                confidence=0.9,
                evidence_ids=[e.id for e in structure_evidence],
                category="architecture",
            )
            self.evidence_store.add_claim(claim)
        
        # Generate dependency claims
        dep_evidence = [e for e in self.evidence_store.evidence.values() 
                       if ":imports" in e.source]
        if dep_evidence:
            all_imports = []
            for e in dep_evidence:
                all_imports.extend(e.metadata.get("imports", []))
            
            claim = Claim(
                id=str(uuid.uuid4()),
                statement=f"Project uses {len(set(all_imports))} unique imports",
                confidence=0.85,
                evidence_ids=[e.id for e in dep_evidence],
                category="dependencies",
            )
            self.evidence_store.add_claim(claim)
        
        # Generate file exploration claims
        explored_files = list(self.coverage_tracker.explored_files)
        if explored_files:
            claim = Claim(
                id=str(uuid.uuid4()),
                statement=f"Explored {len(explored_files)} files in the project",
                confidence=1.0,
                evidence_ids=[],
                category="structure",
            )
            self.evidence_store.add_claim(claim)
    
    def get_report(self) -> dict[str, Any]:
        """Get a comprehensive report of the analysis"""
        return {
            "project_path": str(self.project_path),
            "evidence_summary": self.evidence_store.get_summary(),
            "coverage_summary": self.coverage_tracker.get_summary(),
            "claims": [c.to_dict() for c in self.evidence_store.claims.values()],
            "unsupported_claims": [c.to_dict() for c in self.evidence_store.get_unsupported_claims()],
            "areas": {
                "unexplored": [a.to_dict() for a in self.coverage_tracker.get_unexplored_areas()],
                "partial": [a.to_dict() for a in self.coverage_tracker.get_partial_areas()],
                "complete": [a.to_dict() for a in self.coverage_tracker.get_complete_areas()],
            },
        }
