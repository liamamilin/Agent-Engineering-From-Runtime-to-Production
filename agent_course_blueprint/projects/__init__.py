"""Project Understanding Agent - Capstone Project"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent import ProjectUnderstandingAgent
from evidence import Evidence, Claim, EvidenceStore
from coverage import CoverageTracker, ExplorationArea
from tools import (
    list_files,
    read_file,
    search_code,
    analyze_structure,
)

__all__ = [
    "ProjectUnderstandingAgent",
    "Evidence",
    "Claim",
    "EvidenceStore",
    "CoverageTracker",
    "ExplorationArea",
    "list_files",
    "read_file",
    "search_code",
    "analyze_structure",
]
