"""Progress tracking for interview preparation using database."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .database import DatabaseManager

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Manages learning progress tracking in database."""

    def __init__(self, db: DatabaseManager):
        """
        Initialize progress tracker.

        Args:
            db: DatabaseManager instance
        """
        self.db = db
        logger.debug("ProgressTracker initialized")

    def get_active_material_id(self) -> str:
        """
        Get the currently active material ID.

        Returns:
            Active material ID

        Raises:
            ValueError: If no active material is set
        """
        result = self.db.fetchone(
            "SELECT id FROM materials WHERE is_active = TRUE LIMIT 1"
        )

        if not result:
            raise ValueError("No active material found")

        return result['id']


    def update_progress(
        self,
        material_id: str,
        question_id: int,
        response: str,
        session_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update progress after answering a question.

        Args:
            material_id: Material ID
            question_id: Question ID
            response: Response type ('correct', 'incorrect', 'partial', 'skipped')
            session_id: Optional session ID
            notes: Optional notes

        Returns:
            True if successful
        """
        try:
            # Get question details
            question = self.db.fetchone(
                "SELECT section, subsection, question_number FROM questions WHERE id = ?",
                (question_id,)
            )

            if not question:
                logger.error(f"Question {question_id} not found")
                return False

            # Get attempt number
            attempt_count = self.db.count_records(
                "progress",
                "question_id = ?",
                (question_id,)
            )

            # Insert progress record
            self.db.execute(
                """INSERT INTO progress (material_id, section, subsection, question_id,
                                        attempt_number, response, session_id, notes, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    material_id,
                    question['section'],
                    question['subsection'],
                    question_id,
                    attempt_count + 1,
                    response,
                    session_id,
                    notes,
                    datetime.now().isoformat()
                )
            )

            logger.info(f"Updated progress for question {question_id}: {response}")
            return True

        except Exception as e:
            logger.error(f"Failed to update progress: {e}", exc_info=True)
            return False

    def get_weak_areas(
        self,
        material_id: Optional[str] = None,
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Get all weak areas (below threshold accuracy).

        Args:
            material_id: Material ID. If None, uses active material.
            threshold: Accuracy threshold (default 0.6)

        Returns:
            List of weak areas with details
        """
        mat_id = material_id or self.get_active_material_id()

        # Get subsection statistics
        results = self.db.fetchall(
            """SELECT
                   section,
                   subsection,
                   COUNT(*) as questions_asked,
                   SUM(CASE WHEN response = 'correct' THEN 1 ELSE 0 END) as questions_correct
               FROM progress
               WHERE material_id = ?
               GROUP BY section, subsection
               HAVING COUNT(*) >= 3""",
            (mat_id,)
        )

        weak_areas = []
        for row in results:
            accuracy = row['questions_correct'] / row['questions_asked']
            if accuracy < threshold:
                weak_areas.append({
                    'section': row['section'],
                    'subsection': row['subsection'],
                    'questionsAsked': row['questions_asked'],
                    'questionsCorrect': row['questions_correct'],
                    'accuracy': round(accuracy, 2)
                })

        return sorted(weak_areas, key=lambda x: x['accuracy'])

    def get_statistics(self, material_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get overall statistics.

        Args:
            material_id: Material ID. If None, uses active material.

        Returns:
            Dictionary with statistics
        """
        mat_id = material_id or self.get_active_material_id()

        # Overall stats
        overall = self.db.fetchone(
            """SELECT
                   COUNT(*) as total_asked,
                   SUM(CASE WHEN response = 'correct' THEN 1 ELSE 0 END) as total_correct
               FROM progress
               WHERE material_id = ?""",
            (mat_id,)
        )

        total_asked = overall['total_asked'] or 0
        total_correct = overall['total_correct'] or 0

        # Weak/strong areas
        weak_areas = self.get_weak_areas(mat_id, threshold=0.6)
        strong_subsections = self.db.fetchall(
            """SELECT section, subsection, COUNT(*) as asked
               FROM progress
               WHERE material_id = ?
               GROUP BY section, subsection
               HAVING COUNT(*) >= 3
               AND CAST(SUM(CASE WHEN response = 'correct' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) > 0.8""",
            (mat_id,)
        )

        # Current position
        current = self.db.fetchone(
            """SELECT section, subsection FROM progress
               WHERE material_id = ?
               ORDER BY timestamp DESC LIMIT 1""",
            (mat_id,)
        )

        return {
            'overallProgress': {
                'totalQuestionsAsked': total_asked,
                'totalQuestionsCorrect': total_correct,
                'accuracy': round(total_correct / total_asked, 2) if total_asked > 0 else 0.0
            },
            'currentSection': current['section'] if current else None,
            'currentSubsection': current['subsection'] if current else None,
            'totalWeakAreas': len(weak_areas),
            'totalStrongAreas': len(strong_subsections)
        }

    def start_session(self, material_id: str) -> int:
        """
        Start a new learning session.

        Args:
            material_id: Material ID

        Returns:
            Session ID
        """
        cursor = self.db.execute(
            """INSERT INTO sessions (material_id, started_at, questions_asked, questions_correct)
               VALUES (?, ?, 0, 0)""",
            (material_id, datetime.now().isoformat())
        )

        session_id = cursor.lastrowid
        logger.info(f"Started session {session_id} for material {material_id}")
        return session_id

    def end_session(self, session_id: int) -> bool:
        """
        End a learning session.

        Args:
            session_id: Session ID

        Returns:
            True if successful
        """
        try:
            # Calculate session stats
            stats = self.db.fetchone(
                """SELECT
                       COUNT(*) as questions_asked,
                       SUM(CASE WHEN response = 'correct' THEN 1 ELSE 0 END) as questions_correct
                   FROM progress
                   WHERE session_id = ?""",
                (session_id,)
            )

            # Update session
            self.db.execute(
                """UPDATE sessions
                   SET ended_at = ?, questions_asked = ?, questions_correct = ?
                   WHERE id = ?""",
                (
                    datetime.now().isoformat(),
                    stats['questions_asked'] or 0,
                    stats['questions_correct'] or 0,
                    session_id
                )
            )

            logger.info(f"Ended session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to end session: {e}", exc_info=True)
            return False

    def reset_progress(self, material_id: str) -> bool:
        """
        Reset progress for a material.

        Args:
            material_id: Material ID

        Returns:
            True if successful
        """
        try:
            self.db.execute(
                "DELETE FROM progress WHERE material_id = ?",
                (material_id,)
            )

            self.db.execute(
                "DELETE FROM sessions WHERE material_id = ?",
                (material_id,)
            )

            logger.info(f"Reset progress for material {material_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset progress: {e}", exc_info=True)
            return False
