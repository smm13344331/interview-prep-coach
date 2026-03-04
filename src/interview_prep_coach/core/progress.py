"""Progress tracking for interview preparation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..config.paths import get_progress_file, ensure_data_files_exist


class ProgressTracker:
    """Manages learning progress tracking."""

    def __init__(self, progress_file: Optional[Path] = None):
        """
        Initialize progress tracker.

        Args:
            progress_file: Path to progress JSON file. Uses default if None.
        """
        self.progress_file = progress_file or get_progress_file()
        ensure_data_files_exist()

    def load_progress(self) -> Dict[str, Any]:
        """
        Load progress from JSON file.

        Returns:
            Progress dictionary
        """
        if not self.progress_file.exists():
            ensure_data_files_exist()

        with open(self.progress_file, 'r') as f:
            return json.load(f)

    def save_progress(self, progress: Dict[str, Any]) -> None:
        """
        Save progress to JSON file.

        Args:
            progress: Progress dictionary to save
        """
        progress['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)

    def update_progress(
        self,
        section: str,
        subsection: str,
        question_number: int,
        correct: bool,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update progress after answering a question.

        Args:
            section: Section name (e.g., "Java Core Concepts")
            subsection: Subsection name (e.g., "Memory Management & Garbage Collection")
            question_number: Question number answered
            correct: Whether answer was correct
            notes: Optional notes about the answer

        Returns:
            Updated progress dictionary
        """
        progress = self.load_progress()

        # Update subsection stats
        if section in progress['sections'] and subsection in progress['sections'][section]['subsections']:
            subsection_data = progress['sections'][section]['subsections'][subsection]
            subsection_data['questionsAsked'] += 1
            if correct:
                subsection_data['questionsCorrect'] += 1
            subsection_data['lastQuestionNumber'] = question_number

            # Update section stats
            section_data = progress['sections'][section]
            section_data['overallQuestionsAsked'] += 1
            if correct:
                section_data['overallQuestionsCorrect'] += 1

            # Update overall stats
            progress['overallProgress']['totalQuestionsAsked'] += 1
            if correct:
                progress['overallProgress']['totalQuestionsCorrect'] += 1

            # Recalculate accuracy
            total_asked = progress['overallProgress']['totalQuestionsAsked']
            total_correct = progress['overallProgress']['totalQuestionsCorrect']
            if total_asked > 0:
                progress['overallProgress']['accuracy'] = round(total_correct / total_asked, 2)

            # Update current position
            progress['currentSection'] = section
            progress['currentSubsection'] = subsection

            # Add to session history
            if 'sessionHistory' not in progress:
                progress['sessionHistory'] = []

            progress['sessionHistory'].append({
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'section': section,
                'subsection': subsection,
                'questionNumber': question_number,
                'correct': correct,
                'notes': notes
            })

            # Update weak/strong areas
            self._update_areas(progress, section, subsection)

        self.save_progress(progress)
        return progress

    def _update_areas(self, progress: Dict[str, Any], section: str, subsection: str) -> None:
        """
        Update weak and strong areas based on performance.

        Args:
            progress: Progress dictionary
            section: Section name
            subsection: Subsection name
        """
        section_data = progress['sections'][section]
        subsection_data = section_data['subsections'][subsection]

        asked = subsection_data['questionsAsked']
        correct = subsection_data['questionsCorrect']

        # Only evaluate after at least 3 questions
        if asked < 3:
            return

        accuracy = correct / asked

        area_name = f"{section} - {subsection}"

        # Weak area: less than 60% accuracy
        if accuracy < 0.6:
            if area_name not in section_data['weakAreas']:
                section_data['weakAreas'].append(area_name)
            # Remove from strong areas if present
            if area_name in section_data['strongAreas']:
                section_data['strongAreas'].remove(area_name)

        # Strong area: more than 80% accuracy
        elif accuracy > 0.8:
            if area_name not in section_data['strongAreas']:
                section_data['strongAreas'].append(area_name)
            # Remove from weak areas if present
            if area_name in section_data['weakAreas']:
                section_data['weakAreas'].remove(area_name)

    def get_weak_areas(self) -> List[Dict[str, Any]]:
        """
        Get all weak areas across all sections.

        Returns:
            List of weak areas with details
        """
        progress = self.load_progress()
        weak_areas = []

        for section_name, section_data in progress['sections'].items():
            for weak_area in section_data.get('weakAreas', []):
                # Extract subsection name
                if ' - ' in weak_area:
                    _, subsection = weak_area.split(' - ', 1)
                else:
                    subsection = weak_area

                # Get subsection stats
                if subsection in section_data['subsections']:
                    subsection_data = section_data['subsections'][subsection]
                    accuracy = 0
                    if subsection_data['questionsAsked'] > 0:
                        accuracy = subsection_data['questionsCorrect'] / subsection_data['questionsAsked']

                    weak_areas.append({
                        'section': section_name,
                        'subsection': subsection,
                        'questionsAsked': subsection_data['questionsAsked'],
                        'questionsCorrect': subsection_data['questionsCorrect'],
                        'accuracy': round(accuracy, 2)
                    })

        return weak_areas

    def get_next_question_location(self) -> tuple[str, str, int]:
        """
        Get the next question location (section, subsection, question number).

        Returns:
            Tuple of (section, subsection, next_question_number)
        """
        progress = self.load_progress()
        section = progress.get('currentSection', 'Java Core Concepts')
        subsection = progress.get('currentSubsection', 'Memory Management & Garbage Collection')

        if section in progress['sections'] and subsection in progress['sections'][section]['subsections']:
            last_q = progress['sections'][section]['subsections'][subsection].get('lastQuestionNumber', 0)
            next_q = last_q + 1
        else:
            next_q = 1

        return section, subsection, next_q

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics.

        Returns:
            Dictionary with statistics
        """
        progress = self.load_progress()
        return {
            'overallProgress': progress.get('overallProgress', {}),
            'currentSection': progress.get('currentSection'),
            'currentSubsection': progress.get('currentSubsection'),
            'totalWeakAreas': sum(
                len(section.get('weakAreas', []))
                for section in progress['sections'].values()
            ),
            'totalStrongAreas': sum(
                len(section.get('strongAreas', []))
                for section in progress['sections'].values()
            )
        }

    def reset_progress(self) -> None:
        """Reset progress to initial state."""
        ensure_data_files_exist()
        # Force recreate by removing and calling ensure again
        if self.progress_file.exists():
            self.progress_file.unlink()
        ensure_data_files_exist()
