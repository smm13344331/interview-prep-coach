"""Question retrieval from database."""

import logging
from typing import Dict, List, Optional, Any

from .database import DatabaseManager

logger = logging.getLogger(__name__)


class QuestionParser:
    """
    Retrieves interview questions from database.

    Provides interface for querying questions by section, subsection,
    and performing searches across material.
    """

    def __init__(self, db: DatabaseManager, material_id: Optional[str] = None):
        """
        Initialize question parser.

        Args:
            db: DatabaseManager instance
            material_id: Material ID to query. If None, uses active material.
        """
        self.db = db
        self._material_id = material_id
        logger.debug(f"QuestionParser initialized with material_id: {material_id}")

    def get_active_material_id(self) -> str:
        """
        Get the currently active material ID.

        Returns:
            Active material ID

        Raises:
            ValueError: If no active material is set
        """
        if self._material_id:
            return self._material_id

        result = self.db.fetchone(
            "SELECT id FROM materials WHERE is_active = TRUE LIMIT 1"
        )

        if not result:
            raise ValueError("No active material found. Please activate a material source.")

        return result['id']

    def get_sections(self, material_id: Optional[str] = None) -> List[str]:
        """
        Get list of all section names.

        Args:
            material_id: Material ID to query. If None, uses active material.

        Returns:
            List of section names
        """
        mat_id = material_id or self.get_active_material_id()

        results = self.db.fetchall(
            "SELECT DISTINCT section FROM questions WHERE material_id = ? ORDER BY section",
            (mat_id,)
        )

        return [r['section'] for r in results]

    def get_subsections(self, section: str, material_id: Optional[str] = None) -> List[str]:
        """
        Get list of subsection names for a section.

        Args:
            section: Section name
            material_id: Material ID to query. If None, uses active material.

        Returns:
            List of subsection names
        """
        mat_id = material_id or self.get_active_material_id()

        results = self.db.fetchall(
            """SELECT DISTINCT subsection FROM questions
               WHERE material_id = ? AND section = ?
               ORDER BY subsection""",
            (mat_id, section)
        )

        return [r['subsection'] for r in results]

    def get_question(
        self,
        section: str,
        subsection: str,
        question_number: int,
        material_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific question by location.

        Args:
            section: Section name
            subsection: Subsection name
            question_number: Question number (1-indexed)
            material_id: Material ID to query. If None, uses active material.

        Returns:
            Question dictionary or None if not found
        """
        mat_id = material_id or self.get_active_material_id()

        result = self.db.fetchone(
            """SELECT id, section, subsection, question_number, question_text,
                      answer_text, difficulty, tags
               FROM questions
               WHERE material_id = ? AND section = ? AND subsection = ? AND question_number = ?""",
            (mat_id, section, subsection, question_number)
        )

        if not result:
            return None

        return {
            'id': result['id'],
            'section': result['section'],
            'subsection': result['subsection'],
            'number': result['question_number'],
            'question': result['question_text'],
            'answer': result['answer_text'],
            'fullText': f"Q: {result['question_text']}\n\n{result['answer_text']}",
            'difficulty': result['difficulty'],
            'tags': result['tags']
        }

    def get_next_question(
        self,
        section: str,
        subsection: str,
        last_question_number: int = 0,
        material_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the next question in a subsection.

        Args:
            section: Section name
            subsection: Subsection name
            last_question_number: Last question number answered (0 for first)
            material_id: Material ID to query. If None, uses active material.

        Returns:
            Next question dictionary or None if no more questions
        """
        return self.get_question(section, subsection, last_question_number + 1, material_id)

    def get_all_questions_in_subsection(
        self,
        section: str,
        subsection: str,
        material_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all questions in a subsection.

        Args:
            section: Section name
            subsection: Subsection name
            material_id: Material ID to query. If None, uses active material.

        Returns:
            List of question dictionaries
        """
        mat_id = material_id or self.get_active_material_id()

        results = self.db.fetchall(
            """SELECT id, section, subsection, question_number, question_text,
                      answer_text, difficulty, tags
               FROM questions
               WHERE material_id = ? AND section = ? AND subsection = ?
               ORDER BY question_number""",
            (mat_id, section, subsection)
        )

        return [
            {
                'id': r['id'],
                'section': r['section'],
                'subsection': r['subsection'],
                'number': r['question_number'],
                'question': r['question_text'],
                'answer': r['answer_text'],
                'fullText': f"Q: {r['question_text']}\n\n{r['answer_text']}",
                'difficulty': r['difficulty'],
                'tags': r['tags']
            }
            for r in results
        ]

    def get_question_count(
        self,
        section: Optional[str] = None,
        subsection: Optional[str] = None,
        material_id: Optional[str] = None
    ) -> int:
        """
        Get count of questions.

        Args:
            section: Optional section to filter by
            subsection: Optional subsection to filter by (requires section)
            material_id: Material ID to query. If None, uses active material.

        Returns:
            Number of questions
        """
        mat_id = material_id or self.get_active_material_id()

        if section and subsection:
            return self.db.count_records(
                "questions",
                "material_id = ? AND section = ? AND subsection = ?",
                (mat_id, section, subsection)
            )

        if section:
            return self.db.count_records(
                "questions",
                "material_id = ? AND section = ?",
                (mat_id, section)
            )

        # Total across all sections
        return self.db.count_records(
            "questions",
            "material_id = ?",
            (mat_id,)
        )

    def search_questions(
        self,
        keyword: str,
        material_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for questions containing a keyword using full-text search.

        Args:
            keyword: Keyword to search for
            material_id: Material ID to query. If None, uses active material.

        Returns:
            List of matching questions with location info
        """
        mat_id = material_id or self.get_active_material_id()

        # Use FTS for efficient searching
        results = self.db.fetchall(
            """SELECT q.id, q.section, q.subsection, q.question_number,
                      q.question_text, q.answer_text, q.difficulty, q.tags
               FROM questions q
               JOIN questions_fts ON q.id = questions_fts.rowid
               WHERE questions_fts MATCH ? AND q.material_id = ?
               ORDER BY q.section, q.subsection, q.question_number""",
            (keyword, mat_id)
        )

        return [
            {
                'id': r['id'],
                'section': r['section'],
                'subsection': r['subsection'],
                'number': r['question_number'],
                'question': r['question_text'],
                'answer': r['answer_text'],
                'fullText': f"Q: {r['question_text']}\n\n{r['answer_text']}",
                'difficulty': r['difficulty'],
                'tags': r['tags']
            }
            for r in results
        ]
