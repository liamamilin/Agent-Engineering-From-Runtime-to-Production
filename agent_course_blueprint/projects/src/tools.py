"""Tools for Project Understanding Agent"""

import os
import re
from pathlib import Path
from typing import Any


def list_files(project_path: str, pattern: str = "**/*") -> dict[str, Any]:
    """List files in the project matching a pattern"""
    project = Path(project_path)
    if not project.exists():
        return {"success": False, "error": f"Project path does not exist: {project_path}"}
    
    try:
        files = []
        for file_path in project.glob(pattern):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(project))
                files.append({
                    "path": rel_path,
                    "size": file_path.stat().st_size,
                    "extension": file_path.suffix,
                })
        
        return {
            "success": True,
            "files": files,
            "count": len(files),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def read_file(project_path: str, file_path: str) -> dict[str, Any]:
    """Read the contents of a file"""
    full_path = Path(project_path) / file_path
    if not full_path.exists():
        return {"success": False, "error": f"File does not exist: {file_path}"}
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "lines": len(content.splitlines()),
            "size": len(content),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_code(project_path: str, pattern: str, file_pattern: str = "**/*.py") -> dict[str, Any]:
    """Search for a pattern in code files"""
    project = Path(project_path)
    if not project.exists():
        return {"success": False, "error": f"Project path does not exist: {project_path}"}
    
    try:
        matches = []
        regex = re.compile(pattern)
        
        for file_path in project.glob(file_pattern):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                rel_path = str(file_path.relative_to(project))
                                matches.append({
                                    "file": rel_path,
                                    "line": line_num,
                                    "content": line.strip(),
                                })
                except Exception:
                    continue
        
        return {
            "success": True,
            "matches": matches,
            "count": len(matches),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_structure(project_path: str) -> dict[str, Any]:
    """Analyze the project structure"""
    project = Path(project_path)
    if not project.exists():
        return {"success": False, "error": f"Project path does not exist: {project_path}"}
    
    try:
        # Count files by type
        file_counts = {}
        total_files = 0
        total_size = 0
        
        for file_path in project.rglob("*"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
                ext = file_path.suffix or "no_extension"
                file_counts[ext] = file_counts.get(ext, 0) + 1
        
        # Find key files
        key_files = []
        key_patterns = [
            "README*", "requirements*.txt", "setup.py", "pyproject.toml",
            "package.json", "Cargo.toml", "go.mod", "pom.xml"
        ]
        for pattern in key_patterns:
            for file_path in project.glob(pattern):
                if file_path.is_file():
                    key_files.append(str(file_path.relative_to(project)))
        
        # Find directories
        directories = []
        for dir_path in project.rglob("*"):
            if dir_path.is_dir() and not dir_path.name.startswith('.'):
                rel_path = str(dir_path.relative_to(project))
                if rel_path:  # Skip root
                    directories.append(rel_path)
        
        return {
            "success": True,
            "total_files": total_files,
            "total_size": total_size,
            "file_types": file_counts,
            "key_files": key_files,
            "directories": directories[:20],  # Limit to first 20
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_imports(project_path: str, file_path: str) -> dict[str, Any]:
    """Extract imports from a Python file"""
    full_path = Path(project_path) / file_path
    if not full_path.exists():
        return {"success": False, "error": f"File does not exist: {file_path}"}
    
    if not file_path.endswith('.py'):
        return {"success": False, "error": "File is not a Python file"}
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        imports = []
        # Match import statements
        import_pattern = re.compile(r'^\s*(?:from\s+(\S+)\s+)?import\s+(\S+)', re.MULTILINE)
        for match in import_pattern.finditer(content):
            module = match.group(1) or match.group(2)
            imports.append(module)
        
        return {
            "success": True,
            "imports": imports,
            "count": len(imports),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
