"""CLI interface for agent systems."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Any, Callable

from agent_course.api.config import Config, ConfigManager
from agent_course.api.service import AgentService
from agent_course.core import TaskSpec
from agent_course.runtime import Agent


@dataclass
class CLICommand:
    """A CLI command."""
    
    name: str
    description: str
    handler: Callable[[argparse.Namespace], int]
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        pass


class CLI:
    """Command-line interface for agent systems."""
    
    def __init__(self, name: str = "agent-cli") -> None:
        """Initialize CLI.
        
        Args:
            name: CLI name.
        """
        self._name = name
        self._commands: dict[str, CLICommand] = {}
        self._agent: Agent | None = None
        self._service: AgentService | None = None
        self._config: Config | None = None
    
    def add_command(self, command: CLICommand) -> None:
        """Add a command.
        
        Args:
            command: The command to add.
        """
        self._commands[command.name] = command
    
    def set_agent(self, agent: Agent) -> None:
        """Set the agent.
        
        Args:
            agent: The agent.
        """
        self._agent = agent
    
    def set_service(self, service: AgentService) -> None:
        """Set the service.
        
        Args:
            service: The service.
        """
        self._service = service
    
    def set_config(self, config: Config) -> None:
        """Set the configuration.
        
        Args:
            config: The configuration.
        """
        self._config = config
    
    def run(self, args: list[str] | None = None) -> int:
        """Run the CLI.
        
        Args:
            args: Command-line arguments.
            
        Returns:
            Exit code.
        """
        parser = argparse.ArgumentParser(prog=self._name)
        subparsers = parser.add_subparsers(dest="command", help="Commands")
        
        # Add commands
        for cmd_name, cmd in self._commands.items():
            cmd_parser = subparsers.add_parser(cmd_name, help=cmd.description)
            cmd.add_arguments(cmd_parser)
        
        # Parse arguments
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return 1
        
        # Execute command
        cmd = self._commands.get(parsed_args.command)
        if cmd:
            return cmd.handler(parsed_args)
        
        parser.print_help()
        return 1
    
    @staticmethod
    def create_default_cli() -> CLI:
        """Create a default CLI with standard commands.
        
        Returns:
            CLI instance.
        """
        cli = CLI()
        
        # Run command
        def run_handler(args: argparse.Namespace) -> int:
            if not cli._agent:
                print("Error: Agent not set")
                return 1
            
            task = TaskSpec(goal=args.task, max_steps=args.max_steps)
            result = cli._agent.run(task)
            
            if result.success:
                print(f"Success: {result.output}")
            else:
                print(f"Failed: {result.output}")
                if result.error:
                    print(f"Error: {result.error}")
            
            return 0 if result.success else 1
        
        run_cmd = CLICommand(
            name="run",
            description="Run a task",
            handler=run_handler,
        )
        cli.add_command(run_cmd)
        
        # Serve command
        def serve_handler(args: argparse.Namespace) -> int:
            if not cli._service:
                print("Error: Service not set")
                return 1
            
            print(f"Starting service on {args.host}:{args.port}")
            cli._service.start()
            
            return 0
        
        serve_cmd = CLICommand(
            name="serve",
            description="Start the service",
            handler=serve_handler,
        )
        cli.add_command(serve_cmd)
        
        # Status command
        def status_handler(args: argparse.Namespace) -> int:
            if not cli._service:
                print("Error: Service not set")
                return 1
            
            status = cli._service.get_status()
            print(f"Status: {status['status']}")
            print(f"Requests: {status['request_count']}")
            print(f"Errors: {status['error_count']}")
            print(f"Active sessions: {status['active_sessions']}")
            
            return 0
        
        status_cmd = CLICommand(
            name="status",
            description="Get service status",
            handler=status_handler,
        )
        cli.add_command(status_cmd)
        
        return cli
