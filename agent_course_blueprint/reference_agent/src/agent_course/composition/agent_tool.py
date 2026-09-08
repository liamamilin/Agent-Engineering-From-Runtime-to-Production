"""Agent-as-tool pattern for composition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_course.core import TaskSpec, AgentState, Decision, Observation
from agent_course.runtime import Agent
from agent_course.tools.schema import ToolSchema, ToolParameter, ParameterType


@dataclass
class AgentAsTool:
    """Wraps an Agent as a Tool for use by other agents.
    
    This implements the agent-as-tool composition pattern where
    a specialized agent can be invoked as a tool by a coordinator agent.
    """
    
    agent: Agent
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    
    def get_tool_schema(self) -> ToolSchema:
        """Get the tool schema for this agent-as-tool.
        
        Returns:
            ToolSchema describing this agent as a tool.
        """
        parameters = []
        
        # Add input parameters from schema
        for param_name, param_info in self.input_schema.items():
            param = ToolParameter(
                name=param_name,
                type=ParameterType(param_info.get("type", "string")),
                description=param_info.get("description", ""),
                required=param_info.get("required", True),
            )
            parameters.append(param)
        
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=parameters,
            requires_permission=False,
            idempotent=True,
        )
    
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the agent with given inputs.
        
        Args:
            **kwargs: Input parameters for the agent.
            
        Returns:
            Dictionary with result and metadata.
        """
        # Create task from inputs
        task_description = kwargs.get("task", kwargs.get("query", str(kwargs)))
        task = TaskSpec(
            goal=task_description,
            success_criteria=["Task completed"],
            max_steps=kwargs.get("max_steps", 10),
        )
        
        # Run the agent
        result = self.agent.run(task)
        
        # Format output
        return {
            "result": result.output,
            "success": result.success,
            "termination_reason": result.termination_reason,
            "total_steps": result.total_steps,
            "trace_summary": self._summarize_trace(result.trace) if result.trace else None,
        }
    
    def _summarize_trace(self, trace: Any) -> dict[str, Any]:
        """Summarize trace for output.
        
        Args:
            trace: The execution trace.
            
        Returns:
            Summary of the trace.
        """
        return {
            "total_steps": trace.total_steps,
            "tool_calls": [
                step.decision.get("name")
                for step in trace.steps
                if step.decision.get("kind") == "tool"
            ],
        }


def create_research_agent_tool(model: Any, tools: Any) -> AgentAsTool:
    """Create a research agent wrapped as a tool.
    
    Args:
        model: The model adapter for the agent.
        tools: Tool registry for the agent.
        
    Returns:
        AgentAsTool wrapping a research agent.
    """
    agent = Agent(
        model=model,
        tools=tools,
        system_prompt="You are a research assistant. Search for information and provide concise summaries.",
    )
    
    return AgentAsTool(
        agent=agent,
        name="research_agent",
        description="Research agent that can search and summarize information",
        input_schema={
            "query": {
                "type": "string",
                "description": "The research query",
                "required": True,
            },
        },
        output_schema={
            "result": {
                "type": "string",
                "description": "Research summary",
            },
        },
    )


def create_writer_agent_tool(model: Any) -> AgentAsTool:
    """Create a writer agent wrapped as a tool.
    
    Args:
        model: The model adapter for the agent.
        
    Returns:
        AgentAsTool wrapping a writer agent.
    """
    agent = Agent(
        model=model,
        system_prompt="You are a writing assistant. Help draft, edit, and improve text content.",
    )
    
    return AgentAsTool(
        agent=agent,
        name="writer_agent",
        description="Writing agent that can draft and edit content",
        input_schema={
            "task": {
                "type": "string",
                "description": "The writing task",
                "required": True,
            },
            "context": {
                "type": "string",
                "description": "Context or reference material",
                "required": False,
            },
        },
        output_schema={
            "result": {
                "type": "string",
                "description": "Written content",
            },
        },
    )
