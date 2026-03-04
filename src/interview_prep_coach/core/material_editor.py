"""Material editor for modifying interview questions."""

import re
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime

from ..config.paths import (
    ensure_editable_material_exists,
    get_user_questions_file,
    get_bundled_questions_file,
)


class MaterialEditor:
    """Handles editing of interview preparation material."""

    def __init__(self):
        """Initialize material editor."""
        pass

    def ensure_editable_copy(self) -> Path:
        """
        Ensure user has an editable copy of the material.

        Returns:
            Path to editable material file
        """
        return ensure_editable_material_exists()

    def read_material(self) -> str:
        """
        Read the current material content.

        Returns:
            Full content of the material file
        """
        material_file = get_user_questions_file()
        if material_file.exists():
            with open(material_file, 'r', encoding='utf-8') as f:
                return f.read()

        # Fall back to bundled version
        bundled_file = get_bundled_questions_file()
        with open(bundled_file, 'r', encoding='utf-8') as f:
            return f.read()

    def write_material(self, content: str) -> None:
        """
        Write content to editable material file.

        Args:
            content: Full content to write
        """
        material_file = self.ensure_editable_copy()
        with open(material_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def find_question_location(
        self,
        content: str,
        section: str,
        subsection: str,
        question_number: int
    ) -> Optional[tuple[int, int]]:
        """
        Find the start and end position of a specific question.

        Args:
            content: Material content
            section: Section name
            subsection: Subsection name
            question_number: Question number (1-indexed)

        Returns:
            Tuple of (start_pos, end_pos) or None if not found
        """
        # Find section
        section_pattern = rf'^## {re.escape(section)}$'
        section_match = re.search(section_pattern, content, re.MULTILINE)
        if not section_match:
            return None

        # Find subsection after section
        subsection_pattern = rf'^### {re.escape(subsection)}$'
        subsection_match = re.search(
            subsection_pattern,
            content[section_match.end():],
            re.MULTILINE
        )
        if not subsection_match:
            return None

        subsection_start = section_match.end() + subsection_match.end()

        # Find the Nth question after subsection
        question_pattern = r'\n\*\*Q:'
        matches = list(re.finditer(question_pattern, content[subsection_start:]))

        if question_number < 1 or question_number > len(matches):
            return None

        question_start = subsection_start + matches[question_number - 1].start()

        # Find end of question (next question or next section/subsection)
        if question_number < len(matches):
            # End at next question
            question_end = subsection_start + matches[question_number].start()
        else:
            # Find next ### or ## or end of file
            next_heading = re.search(
                r'\n#{2,3} ',
                content[question_start + 1:]
            )
            if next_heading:
                question_end = question_start + 1 + next_heading.start()
            else:
                question_end = len(content)

        return (question_start, question_end)

    def edit_question(
        self,
        section: str,
        subsection: str,
        question_number: int,
        new_question: Optional[str] = None,
        new_answer: Optional[str] = None
    ) -> bool:
        """
        Edit a specific question's text or answer.

        Args:
            section: Section name
            subsection: Subsection name
            question_number: Question number to edit
            new_question: New question text (None to keep existing)
            new_answer: New answer text (None to keep existing)

        Returns:
            True if successful, False if question not found
        """
        content = self.read_material()
        location = self.find_question_location(content, section, subsection, question_number)

        if not location:
            return False

        start_pos, end_pos = location
        question_block = content[start_pos:end_pos]

        # Parse current question
        q_match = re.match(r'\n\*\*Q:\s*([^\n]+)\*\*', question_block)
        if not q_match:
            return False

        current_question = q_match.group(1).strip()
        answer_start = q_match.end()
        current_answer = question_block[answer_start:].strip()

        # Build new question block
        final_question = new_question if new_question is not None else current_question
        final_answer = new_answer if new_answer is not None else current_answer

        new_block = f"\n**Q: {final_question}**\n{final_answer}\n"

        # Replace in content
        new_content = content[:start_pos] + new_block + content[end_pos:]
        self.write_material(new_content)

        return True

    def add_question(
        self,
        section: str,
        subsection: str,
        question: str,
        answer: str,
        position: Optional[int] = None
    ) -> bool:
        """
        Add a new question to a subsection.

        Args:
            section: Section name
            subsection: Subsection name
            question: Question text
            answer: Answer text
            position: Position to insert (None = append to end)

        Returns:
            True if successful, False if section/subsection not found
        """
        content = self.read_material()

        # Find section
        section_pattern = rf'^## {re.escape(section)}$'
        section_match = re.search(section_pattern, content, re.MULTILINE)
        if not section_match:
            return False

        # Find subsection
        subsection_pattern = rf'^### {re.escape(subsection)}$'
        subsection_match = re.search(
            subsection_pattern,
            content[section_match.end():],
            re.MULTILINE
        )
        if not subsection_match:
            return False

        subsection_start = section_match.end() + subsection_match.end()

        # Find insertion point
        if position is None:
            # Append to end of subsection
            # Find next ### or ## or ---
            next_section = re.search(
                r'\n(?:#{2,3} |---\n)',
                content[subsection_start:]
            )
            if next_section:
                insert_pos = subsection_start + next_section.start()
            else:
                insert_pos = len(content)
        else:
            # Insert at specific position
            location = self.find_question_location(content, section, subsection, position)
            if location:
                insert_pos = location[0]
            else:
                # Position doesn't exist, append to end
                next_section = re.search(
                    r'\n(?:#{2,3} |---\n)',
                    content[subsection_start:]
                )
                if next_section:
                    insert_pos = subsection_start + next_section.start()
                else:
                    insert_pos = len(content)

        # Create new question block
        new_question = f"\n**Q: {question}**\n{answer}\n"

        # Insert into content
        new_content = content[:insert_pos] + new_question + content[insert_pos:]
        self.write_material(new_content)

        return True

    def apply_improvement(
        self,
        improvement: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Apply a logged improvement to the material.

        Args:
            improvement: Improvement dictionary from improvement log

        Returns:
            Tuple of (success, message)
        """
        improvement_type = improvement.get('type')
        section = improvement.get('section')
        subsection = improvement.get('subsection')
        question_number = improvement.get('questionNumber')
        description = improvement.get('description', '')

        # Parse description for specific changes
        # This is a heuristic - coach can provide structured changes in description

        if improvement_type == 'unclear_question':
            # Improvement should describe clearer wording
            if not question_number:
                return False, "Question number required for unclear_question type"

            # Look for "Change to:" or "Should be:" in description
            new_q_match = re.search(r'(?:change to|should be|rewrite as):\s*["\']?([^"\']+)["\']?', description, re.IGNORECASE)
            if new_q_match:
                new_question = new_q_match.group(1).strip()
                if self.edit_question(section, subsection, question_number, new_question=new_question):
                    return True, f"Updated question {question_number} in {section} - {subsection}"
                return False, "Question not found"

            return False, "Could not parse new question text from description"

        elif improvement_type == 'answer_issue':
            # Improvement should describe better answer
            if not question_number:
                return False, "Question number required for answer_issue type"

            # Look for answer changes in description
            new_a_match = re.search(r'(?:answer:|should include:|add:)\s*(.+)', description, re.IGNORECASE | re.DOTALL)
            if new_a_match:
                new_answer = new_a_match.group(1).strip()
                if self.edit_question(section, subsection, question_number, new_answer=new_answer):
                    return True, f"Updated answer for question {question_number}"
                return False, "Question not found"

            return False, "Could not parse new answer from description"

        elif improvement_type == 'missing_topic':
            # Add a new question
            # Parse question and answer from description
            q_match = re.search(r'(?:question|Q):\s*(.+?)(?:\n|answer|A:)', description, re.IGNORECASE)
            a_match = re.search(r'(?:answer|A):\s*(.+)', description, re.IGNORECASE | re.DOTALL)

            if q_match and a_match:
                question = q_match.group(1).strip()
                answer = a_match.group(1).strip()

                if self.add_question(section, subsection, question, answer):
                    return True, f"Added new question to {section} - {subsection}"
                return False, "Section/subsection not found"

            return False, "Could not parse question/answer from description"

        elif improvement_type == 'outdated_info':
            # Similar to unclear_question, but might affect answer more
            if not question_number:
                return False, "Question number required"

            # Look for updates in description
            update_match = re.search(r'(?:update to|change to|should mention):\s*(.+)', description, re.IGNORECASE | re.DOTALL)
            if update_match:
                new_info = update_match.group(1).strip()
                # Assume it's answer update for outdated info
                if self.edit_question(section, subsection, question_number, new_answer=new_info):
                    return True, f"Updated outdated information in question {question_number}"
                return False, "Question not found"

            return False, "Could not parse update from description"

        else:
            return False, f"Improvement type '{improvement_type}' not yet supported for auto-apply"

    def reset_to_bundled(self) -> bool:
        """
        Reset material to bundled version, discarding user edits.

        Returns:
            True if successful
        """
        user_file = get_user_questions_file()
        if user_file.exists():
            user_file.unlink()
        return True

    def export_material(self, export_path: Path) -> bool:
        """
        Export current material to a file.

        Args:
            export_path: Path to export to

        Returns:
            True if successful
        """
        try:
            content = self.read_material()
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False

    def get_material_info(self) -> Dict[str, Any]:
        """
        Get information about the current material.

        Returns:
            Dictionary with material metadata
        """
        user_file = get_user_questions_file()
        using_custom = user_file.exists()

        if using_custom:
            material_file = user_file
            source = "user-edited"
        else:
            material_file = get_bundled_questions_file()
            source = "bundled"

        # Get file stats
        stats = material_file.stat()

        return {
            'source': source,
            'path': str(material_file),
            'size_bytes': stats.st_size,
            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'editable': True  # Can always edit by creating copy
        }
