"""CLI for Project Understanding Agent"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import click
import json

from agent import ProjectUnderstandingAgent
from tools import list_files as list_files_tool, analyze_structure
from agent_course.llm import FakeModel


@click.group()
def cli():
    """Project Understanding Agent CLI"""
    pass


@cli.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--goal', default='Understand the project structure and architecture',
              help='Analysis goal')
@click.option('--output', type=click.Path(), help='Output file for report')
@click.option('--mock', is_flag=True, help='Use mock model for testing')
def analyze(project_path, goal, output, mock):
    """Analyze a project repository"""
    click.echo(f"Analyzing project: {project_path}")
    click.echo(f"Goal: {goal}")
    
    # Create model
    if mock:
        from agent_course.llm import ModelResponse
        model = FakeModel(responses=[
            ModelResponse(content="I'll analyze the project structure"),
            ModelResponse(
                content="",
                tool_calls=[{
                    "id": "call_1",
                    "name": "analyze_structure",
                    "arguments": {},
                }],
            ),
            ModelResponse(content="The project is a Python application with 10 files."),
        ])
    else:
        # In production, you would use a real model
        # For now, use mock model
        click.echo("Note: Using mock model. In production, configure a real LLM.")
        model = FakeModel(responses=[
            ModelResponse(content="Project analysis complete."),
        ])
    
    # Create agent
    agent = ProjectUnderstandingAgent(model, project_path)
    
    # Run analysis
    click.echo("\nStarting analysis...")
    result = agent.analyze(goal=goal)
    
    # Display results
    click.echo("\n=== Analysis Complete ===")
    click.echo(f"Success: {result['success']}")
    
    click.echo("\n--- Evidence Summary ---")
    evidence_summary = result['evidence_summary']
    click.echo(f"Total evidence: {evidence_summary['total_evidence']}")
    
    click.echo("\n--- Coverage Summary ---")
    coverage_summary = result['coverage_summary']
    click.echo(f"Coverage: {coverage_summary['coverage_percentage']:.1%}")
    click.echo(f"Explored files: {coverage_summary['explored_files']}/{coverage_summary['total_files']}")
    
    click.echo("\n--- Claims ---")
    for claim in result['claims']:
        click.echo(f"[{claim['confidence']:.0%}] {claim['statement']}")
        click.echo(f"  Category: {claim['category']}")
        click.echo(f"  Evidence: {len(claim['evidence_ids'])} items")
    
    # Save report if output specified
    if output:
        report = agent.get_report()
        with open(output, 'w') as f:
            json.dump(report, f, indent=2)
        click.echo(f"\nReport saved to: {output}")


@cli.command()
@click.argument('project_path', type=click.Path(exists=True))
def list_files(project_path):
    """List files in a project"""
    result = list_files_tool(project_path)
    
    if result['success']:
        click.echo(f"Found {result['count']} files:")
        for file_info in result['files'][:20]:  # Show first 20
            click.echo(f"  {file_info['path']} ({file_info['size']} bytes)")
        if result['count'] > 20:
            click.echo(f"  ... and {result['count'] - 20} more")
    else:
        click.echo(f"Error: {result['error']}")


@cli.command()
@click.argument('project_path', type=click.Path(exists=True))
def structure(project_path):
    """Analyze project structure"""
    result = analyze_structure(project_path)
    
    if result['success']:
        click.echo("=== Project Structure ===")
        click.echo(f"Total files: {result['total_files']}")
        click.echo(f"Total size: {result['total_size']} bytes")
        
        click.echo("\nFile types:")
        for ext, count in sorted(result['file_types'].items()):
            click.echo(f"  {ext}: {count}")
        
        if result['key_files']:
            click.echo("\nKey files:")
            for key_file in result['key_files']:
                click.echo(f"  {key_file}")
        
        click.echo(f"\nDirectories: {len(result['directories'])}")
    else:
        click.echo(f"Error: {result['error']}")


if __name__ == '__main__':
    cli()
