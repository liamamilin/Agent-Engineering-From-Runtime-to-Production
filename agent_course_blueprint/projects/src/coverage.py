"""Coverage tracking for Project Understanding Agent"""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class ExplorationStatus(Enum):
    """Status of exploration for an area"""
    UNEXPLORED = "unexplored"
    PARTIAL = "partial"
    COMPLETE = "complete"


@dataclass
class ExplorationArea:
    """An area of the project that can be explored"""
    name: str
    description: str
    status: ExplorationStatus = ExplorationStatus.UNEXPLORED
    files_explored: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "files_explored": self.files_explored,
            "findings": self.findings,
        }


@dataclass
class CoverageTracker:
    """Tracks exploration coverage of a project"""
    areas: dict[str, ExplorationArea] = field(default_factory=dict)
    total_files: int = 0
    explored_files: set[str] = field(default_factory=set)
    
    def add_area(self, area: ExplorationArea) -> None:
        """Add an exploration area"""
        self.areas[area.name] = area
    
    def mark_file_explored(self, file_path: str, area_name: str) -> None:
        """Mark a file as explored in a specific area"""
        self.explored_files.add(file_path)
        if area_name in self.areas:
            area = self.areas[area_name]
            if file_path not in area.files_explored:
                area.files_explored.append(file_path)
                if len(area.files_explored) > 0:
                    area.status = ExplorationStatus.PARTIAL
    
    def add_finding(self, area_name: str, finding: str) -> None:
        """Add a finding to an area"""
        if area_name in self.areas:
            self.areas[area_name].findings.append(finding)
    
    def mark_area_complete(self, area_name: str) -> None:
        """Mark an area as completely explored"""
        if area_name in self.areas:
            self.areas[area_name].status = ExplorationStatus.COMPLETE
    
    def get_coverage_percentage(self) -> float:
        """Get overall coverage percentage"""
        if self.total_files == 0:
            return 0.0
        return len(self.explored_files) / self.total_files
    
    def get_unexplored_areas(self) -> list[ExplorationArea]:
        """Get areas that haven't been explored"""
        return [a for a in self.areas.values() 
                if a.status == ExplorationStatus.UNEXPLORED]
    
    def get_partial_areas(self) -> list[ExplorationArea]:
        """Get areas that are partially explored"""
        return [a for a in self.areas.values() 
                if a.status == ExplorationStatus.PARTIAL]
    
    def get_complete_areas(self) -> list[ExplorationArea]:
        """Get areas that are completely explored"""
        return [a for a in self.areas.values() 
                if a.status == ExplorationStatus.COMPLETE]
    
    def get_summary(self) -> dict[str, Any]:
        """Get coverage summary"""
        return {
            "total_files": self.total_files,
            "explored_files": len(self.explored_files),
            "coverage_percentage": self.get_coverage_percentage(),
            "total_areas": len(self.areas),
            "unexplored_areas": len(self.get_unexplored_areas()),
            "partial_areas": len(self.get_partial_areas()),
            "complete_areas": len(self.get_complete_areas()),
        }
    
    def initialize_default_areas(self) -> None:
        """Initialize default exploration areas"""
        default_areas = [
            ExplorationArea(
                name="structure",
                description="Project structure and organization",
            ),
            ExplorationArea(
                name="dependencies",
                description="External dependencies and imports",
            ),
            ExplorationArea(
                name="architecture",
                description="High-level architecture and design patterns",
            ),
            ExplorationArea(
                name="core_logic",
                description="Core business logic and algorithms",
            ),
            ExplorationArea(
                name="configuration",
                description="Configuration and environment setup",
            ),
            ExplorationArea(
                name="testing",
                description="Test coverage and testing patterns",
            ),
        ]
        for area in default_areas:
            self.add_area(area)
