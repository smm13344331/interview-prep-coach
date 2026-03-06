"""Material editor for modifying interview questions in database."""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
from pathlib import Path

from .database import DatabaseManager

logger = logging.getLogger(__name__)


class MaterialEditor:
    """Handles editing of interview preparation material in database."""

    def __init__(self, db: DatabaseManager):
        """
        Initialize material editor.

        Args:
            db: DatabaseManager instance
        """
        self.db = db
        logger.debug("MaterialEditor initialized")

    def edit_question(
        self,
        material_id: str,
        question_id: int,
        new_question: Optional[str] = None,
        new_answer: Optional[str] = None
    ) -> bool:
        """
        Edit a specific question's text or answer.

        Args:
            material_id: Material ID
            question_id: Question ID to edit
            new_question: New question text (None to keep existing)
            new_answer: New answer text (None to keep existing)

        Returns:
            True if successful, False if question not found
        """
        try:
            # Build update query based on what's being changed
            updates = []
            params = []

            if new_question is not None:
                updates.append("question_text = ?")
                params.append(new_question)

            if new_answer is not None:
                updates.append("answer_text = ?")
                params.append(new_answer)

            if not updates:
                logger.warning("No changes specified for question edit")
                return False

            # Always update timestamp
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())

            # Add question_id to params
            params.append(question_id)

            query = f"UPDATE questions SET {', '.join(updates)} WHERE id = ?"
            result = self.db.execute(query, tuple(params))

            if result.rowcount == 0:
                logger.warning(f"Question {question_id} not found")
                return False

            logger.info(f"Updated question {question_id} in material {material_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to edit question: {e}", exc_info=True)
            return False

    def add_question(
        self,
        material_id: str,
        section: str,
        subsection: str,
        question: str,
        answer: str,
        position: Optional[int] = None,
        difficulty: Optional[str] = None,
        tags: Optional[str] = None
    ) -> int:
        """
        Add a new question to a subsection.

        Args:
            material_id: Material ID
            section: Section name
            subsection: Subsection name
            question: Question text
            answer: Answer text
            position: Position to insert (None = append to end)
            difficulty: Optional difficulty level
            tags: Optional comma-separated tags

        Returns:
            Question ID of newly created question, or 0 if failed
        """
        try:
            # Determine question number
            if position is not None:
                question_number = position

                # Shift existing questions up
                self.db.execute(
                    """UPDATE questions
                       SET question_number = question_number + 1
                       WHERE material_id = ? AND section = ? AND subsection = ?
                       AND question_number >= ?""",
                    (material_id, section, subsection, position)
                )
            else:
                # Append to end
                result = self.db.fetchone(
                    """SELECT MAX(question_number) as max_num FROM questions
                       WHERE material_id = ? AND section = ? AND subsection = ?""",
                    (material_id, section, subsection)
                )
                question_number = (result['max_num'] or 0) + 1

            # Insert new question
            cursor = self.db.execute(
                """INSERT INTO questions (material_id, section, subsection, question_number,
                                         question_text, answer_text, difficulty, tags,
                                         created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    material_id,
                    section,
                    subsection,
                    question_number,
                    question,
                    answer,
                    difficulty,
                    tags,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                )
            )

            question_id = cursor.lastrowid
            logger.info(f"Added question {question_id} to {section}/{subsection}")
            return question_id

        except Exception as e:
            logger.error(f"Failed to add question: {e}", exc_info=True)
            return 0

    def delete_question(self, question_id: int) -> bool:
        """
        Delete a question.

        Args:
            question_id: Question ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get question details for renumbering
            question = self.db.fetchone(
                "SELECT material_id, section, subsection, question_number FROM questions WHERE id = ?",
                (question_id,)
            )

            if not question:
                logger.warning(f"Question {question_id} not found")
                return False

            # Delete question
            self.db.execute("DELETE FROM questions WHERE id = ?", (question_id,))

            # Renumber remaining questions in subsection
            self.db.execute(
                """UPDATE questions
                   SET question_number = question_number - 1
                   WHERE material_id = ? AND section = ? AND subsection = ?
                   AND question_number > ?""",
                (
                    question['material_id'],
                    question['section'],
                    question['subsection'],
                    question['question_number']
                )
            )

            logger.info(f"Deleted question {question_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete question: {e}", exc_info=True)
            return False

    def clone_material(
        self,
        source_material_id: str,
        new_material_id: str,
        new_name: str,
        new_description: Optional[str] = None
    ) -> bool:
        """
        Clone an existing material source for customization.

        This is the database equivalent of copy-on-write.

        Args:
            source_material_id: Source material ID to clone
            new_material_id: New material ID
            new_name: Name for new material
            new_description: Optional description

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if source exists
            source = self.db.fetchone(
                "SELECT * FROM materials WHERE id = ?",
                (source_material_id,)
            )

            if not source:
                logger.error(f"Source material {source_material_id} not found")
                return False

            # Check if new material ID already exists
            existing = self.db.fetchone(
                "SELECT id FROM materials WHERE id = ?",
                (new_material_id,)
            )

            if existing:
                logger.error(f"Material {new_material_id} already exists")
                return False

            with self.db.transaction():
                # Create new material entry
                self.db.execute(
                    """INSERT INTO materials (id, name, description, version, source_type, is_active)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        new_material_id,
                        new_name,
                        new_description or f"Cloned from {source['name']}",
                        source['version'],
                        'user',
                        False
                    )
                )

                # Clone all questions
                self.db.execute(
                    """INSERT INTO questions (material_id, section, subsection, question_number,
                                             question_text, answer_text, difficulty, tags,
                                             created_at, updated_at)
                       SELECT ?, section, subsection, question_number,
                              question_text, answer_text, difficulty, tags,
                              ?, ?
                       FROM questions
                       WHERE material_id = ?""",
                    (
                        new_material_id,
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        source_material_id
                    )
                )

            logger.info(f"Cloned material {source_material_id} to {new_material_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to clone material: {e}", exc_info=True)
            return False

    def get_material_info(self, material_id: str) -> Dict[str, Any]:
        """
        Get information about a material.

        Args:
            material_id: Material ID

        Returns:
            Dictionary with material metadata
        """
        try:
            material = self.db.fetchone(
                "SELECT * FROM materials WHERE id = ?",
                (material_id,)
            )

            if not material:
                return {'error': 'Material not found'}

            # Get question count
            question_count = self.db.count_records(
                "questions",
                "material_id = ?",
                (material_id,)
            )

            # Get section count
            sections = self.db.fetchall(
                "SELECT DISTINCT section FROM questions WHERE material_id = ?",
                (material_id,)
            )

            return {
                'id': material['id'],
                'name': material['name'],
                'description': material['description'],
                'version': material['version'],
                'source_type': material['source_type'],
                'is_active': bool(material['is_active']),
                'created_at': material['created_at'],
                'updated_at': material['updated_at'],
                'question_count': question_count,
                'section_count': len(sections)
            }

        except Exception as e:
            logger.error(f"Failed to get material info: {e}", exc_info=True)
            return {'error': str(e)}

    def export_material_to_markdown(self, material_id: str, output_path: Path) -> bool:
        """
        Export material from database to markdown file.

        Args:
            material_id: Material ID to export
            output_path: Path to write markdown file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all questions ordered by section, subsection, question_number
            questions = self.db.fetchall(
                """SELECT section, subsection, question_number, question_text, answer_text
                   FROM questions
                   WHERE material_id = ?
                   ORDER BY section, subsection, question_number""",
                (material_id,)
            )

            if not questions:
                logger.warning(f"No questions found for material {material_id}")
                return False

            # Build markdown content
            lines = []
            current_section = None
            current_subsection = None

            for q in questions:
                # Add section header if changed
                if q['section'] != current_section:
                    if current_section is not None:
                        lines.append('')  # Blank line before new section
                    lines.append(f"## {q['section']}\n")
                    current_section = q['section']
                    current_subsection = None

                # Add subsection header if changed
                if q['subsection'] != current_subsection:
                    lines.append(f"### {q['subsection']}\n")
                    current_subsection = q['subsection']

                # Add question
                lines.append(f"**Q: {q['question_text']}**")
                lines.append(q['answer_text'])
                lines.append('')  # Blank line after answer

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            logger.info(f"Exported material {material_id} to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export material: {e}", exc_info=True)
            return False
