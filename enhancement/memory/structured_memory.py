"""
Structured Memory and Session State scaffold.

Enhancement Layer Component:
- Persists session turns, candidate evaluation dossiers, and candidate shortlist state across interactions.
"""

from typing import Dict, Any, Optional
from pathlib import Path


class StructuredRecruitmentMemory:
    """Manages short-term conversational context and long-term candidate state dossiers."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path

    def save_candidate_state(self, candidate_id: str, state_data: Dict[str, Any]) -> None:
        """Persists candidate screening state. Scheduled for Milestone 5."""
        raise NotImplementedError("Structured memory persistence scheduled for Milestone 5.")

    def get_candidate_state(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached candidate screening state. Scheduled for Milestone 5."""
        raise NotImplementedError("Structured memory retrieval scheduled for Milestone 5.")
