"""CLI tool for file operations"""

import click
from pathlib import Path


@click.group()
def cli():
    """File operations CLI tool"""
    pass


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def count(file_path):
    """Count lines in a file"""
    path = Path(file_path)
    with open(path, 'r') as f:
        lines = f.readlines()
    click.echo(f"Lines: {len(lines)}")


@cli.command()
@click.argument('pattern')
@click.argument('directory', type=click.Path(exists=True))
def search(pattern, directory):
    """Search for pattern in files"""
    dir_path = Path(directory)
    count = 0
    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if pattern in content:
                        click.echo(f"Found in: {file_path}")
                        count += 1
            except Exception:
                continue
    click.echo(f"Total matches: {count}")


if __name__ == '__main__':
    cli()
