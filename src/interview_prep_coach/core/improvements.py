"""Improvement logging for interview preparation material."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..config.paths import get_improvement_file, ensure_data_files_exist


class ImprovementLogger:
    """Manages improvement tracking for interview material."""

    def __init__(self, improvement_file: Optional[Path] = None):
        """
        Initialize improvement logger.

        Args:
            improvement_file: Path to improvement JSON file. Uses default if None.
        """
        self.improvement_file = improvement_file or get_improvement_file()
        ensure_data_files_exist()

    def load_improvements(self) -> Dict[str, Any]:
        """
        Load improvements from JSON file.

        Returns:
            Improvements dictionary
        """
        if not self.improvement_file.exists():
            ensure_data_files_exist()

        with open(self.improvement_file, 'r') as f:
            return json.load(f)

    def save_improvements(self, improvements: Dict[str, Any]) -> None:
        """
        Save improvements to JSON file.

        Args:
            improvements: Improvements dictionary to save
        """
        improvements['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
        with open(self.improvement_file, 'w') as f:
            json.dump(improvements, f, indent=2)

    def log_improvement(
        self,
        section: str,
        subsection: Optional[str],
        improvement_type: str,
        description: str,
        question_number: Optional[int] = None,
        priority: str = "medium",
        suggested_by: str = "user"
    ) -> Dict[str, Any]:
        """
        Log a new improvement.

        Args:
            section: Section name (e.g., "Java Core Concepts")
            subsection: Subsection name or None for section-level improvement
            improvement_type: Type of improvement (unclear_question, missing_topic, etc.)
            description: Detailed description of the improvement
            question_number: Specific question number if applicable
            priority: Priority level (low, medium, high, critical)
            suggested_by: Who suggested it (user, system, coach)

        Returns:
            Created improvement entry
        """
        improvements = self.load_improvements()

        # Generate improvement ID
        improvement_id = improvements['nextImprovementId']
        improvements['nextImprovementId'] += 1

        # Create improvement entry
        improvement_entry = {
            'id': improvement_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'section': section,
            'subsection': subsection,
            'type': improvement_type,
            'description': description,
            'questionNumber': question_number,
            'priority': priority,
            'suggestedBy': suggested_by,
            'status': 'pending',
            'implementedAt': None,
            'implementationNotes': None
        }

        # Add to pending improvements
        improvements['pendingImprovements'].append(improvement_entry)

        # Update type counter
        if improvement_type in improvements['improvementTypes']:
            improvements['improvementTypes'][improvement_type]['count'] += 1

        # Update section counter
        if section in improvements['improvementsBySection']:
            improvements['improvementsBySection'][section]['pending'] += 1

        # Update metrics
        improvements['metrics']['totalImprovementsLogged'] += 1
        if suggested_by == 'user':
            improvements['metrics']['userSuggestions'] += 1
        else:
            improvements['metrics']['systemIdentified'] += 1

        self.save_improvements(improvements)
        return improvement_entry

    def mark_implemented(
        self,
        improvement_id: int,
        implementation_notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Mark an improvement as implemented.

        Args:
            improvement_id: ID of improvement to mark as implemented
            implementation_notes: Notes about the implementation

        Returns:
            Updated improvement entry or None if not found
        """
        improvements = self.load_improvements()

        # Find improvement in pending list
        improvement = None
        for i, imp in enumerate(improvements['pendingImprovements']):
            if imp['id'] == improvement_id:
                improvement = improvements['pendingImprovements'].pop(i)
                break

        if not improvement:
            return None

        # Update improvement
        improvement['status'] = 'implemented'
        improvement['implementedAt'] = datetime.utcnow().isoformat() + 'Z'
        improvement['implementationNotes'] = implementation_notes

        # Move to implemented list
        improvements['implementedImprovements'].append(improvement)

        # Update section counters
        section = improvement['section']
        if section in improvements['improvementsBySection']:
            improvements['improvementsBySection'][section]['pending'] -= 1
            improvements['improvementsBySection'][section]['implemented'] += 1

        # Update metrics
        improvements['metrics']['totalImplemented'] += 1

        # Recalculate implementation rate
        total = improvements['metrics']['totalImprovementsLogged']
        implemented = improvements['metrics']['totalImplemented']
        if total > 0:
            improvements['metrics']['implementationRate'] = round(implemented / total, 2)

        self.save_improvements(improvements)
        return improvement

    def get_pending_improvements(
        self,
        section: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending improvements, optionally filtered.

        Args:
            section: Filter by section name
            priority: Filter by priority level

        Returns:
            List of pending improvements
        """
        improvements = self.load_improvements()
        pending = improvements['pendingImprovements']

        if section:
            pending = [imp for imp in pending if imp['section'] == section]

        if priority:
            pending = [imp for imp in pending if imp['priority'] == priority]

        return pending

    def get_implemented_improvements(
        self,
        section: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get implemented improvements, optionally filtered.

        Args:
            section: Filter by section name

        Returns:
            List of implemented improvements
        """
        improvements = self.load_improvements()
        implemented = improvements['implementedImprovements']

        if section:
            implemented = [imp for imp in implemented if imp['section'] == section]

        return implemented

    def get_improvements_by_type(self) -> Dict[str, int]:
        """
        Get improvement counts by type.

        Returns:
            Dictionary mapping improvement type to count
        """
        improvements = self.load_improvements()
        return {
            imp_type: data['count']
            for imp_type, data in improvements['improvementTypes'].items()
        }

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get improvement metrics.

        Returns:
            Metrics dictionary
        """
        improvements = self.load_improvements()
        return improvements['metrics']

    def add_user_feedback(self, feedback: str) -> None:
        """
        Add general user feedback.

        Args:
            feedback: Feedback text
        """
        improvements = self.load_improvements()

        feedback_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'feedback': feedback
        }

        improvements['userFeedback'].append(feedback_entry)
        self.save_improvements(improvements)
