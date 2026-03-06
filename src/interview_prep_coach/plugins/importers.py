"""Material importers for different file formats."""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from ..core.database import DatabaseManager

logger = logging.getLogger(__name__)


class MarkdownImporter:
    """
    Import interview questions from markdown files.

    Expected format:
    ## Section Name

    ### Subsection Name

    **Q: Question text?**
    Answer text...

    **Q: Another question?**
    Another answer...
    """

    def parse_markdown(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse markdown content into structured questions.

        Args:
            content: Markdown file content

        Returns:
            List of question dictionaries with section, subsection, question, answer
        """
        questions = []
        current_section = None
        current_subsection = None
        question_number = 0

        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Section header (## Section)
            if line.startswith('## ') and not line.startswith('###'):
                current_section = line[3:].strip()
                # Reset subsection, but don't set it to None
                # We'll use a default if questions appear without a subsection
                current_subsection = None
                question_number = 0
                i += 1
                continue

            # Subsection header (### Subsection)
            if line.startswith('### '):
                current_subsection = line[4:].strip()
                question_number = 0
                i += 1
                continue

            # Question (**Q: Question text?**)
            if line.startswith('**Q:') and line.endswith('**'):
                if not current_section:
                    logger.warning(f"Question found without section: {line}")
                    i += 1
                    continue

                # If no subsection is set, use a default based on section
                if not current_subsection:
                    current_subsection = "General"
                    question_number = 0

                # Extract question text
                question_text = line[4:-2].strip()  # Remove **Q: and **
                question_number += 1

                # Collect answer lines until next question or section
                answer_lines = []
                i += 1

                while i < len(lines):
                    next_line = lines[i].strip()

                    # Stop at next section, subsection, or question
                    if (next_line.startswith('##') or
                        next_line.startswith('**Q:') or
                        (i + 1 < len(lines) and lines[i + 1].strip().startswith('##'))):
                        break

                    if next_line:  # Skip empty lines at start
                        answer_lines.append(lines[i].rstrip())
                    elif answer_lines:  # Keep empty lines in middle of answer
                        answer_lines.append('')

                    i += 1

                # Clean up answer text
                answer_text = '\n'.join(answer_lines).strip()

                if answer_text:
                    questions.append({
                        'section': current_section,
                        'subsection': current_subsection,
                        'question_number': question_number,
                        'question_text': question_text,
                        'answer_text': answer_text
                    })
                else:
                    logger.warning(f"Question without answer: {question_text}")

                continue

            i += 1

        logger.info(f"Parsed {len(questions)} questions from markdown")
        return questions

    def import_to_db(self, db: DatabaseManager, material_id: str, file_path: Path) -> int:
        """
        Import questions from markdown file into database.

        Args:
            db: DatabaseManager instance
            material_id: Material ID to associate questions with
            file_path: Path to markdown file

        Returns:
            Number of questions imported
        """
        logger.info(f"Importing markdown from {file_path} as material {material_id}")

        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse questions
        questions = self.parse_markdown(content)

        # Import to database
        count = 0
        for q in questions:
            try:
                db.execute(
                    """INSERT INTO questions (material_id, section, subsection, question_number,
                                             question_text, answer_text, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        material_id,
                        q['section'],
                        q['subsection'],
                        q['question_number'],
                        q['question_text'],
                        q['answer_text'],
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    )
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to import question: {e}\nQuestion: {q}")

        logger.info(f"Imported {count} questions from markdown")
        return count


class JSONImporter:
    """
    Import interview questions from JSON files.

    Expected format:
    {
        "sections": [
            {
                "name": "Section Name",
                "subsections": [
                    {
                        "name": "Subsection Name",
                        "questions": [
                            {
                                "question": "Question text?",
                                "answer": "Answer text",
                                "difficulty": "medium",
                                "tags": ["tag1", "tag2"]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    """

    def parse_json(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse JSON content into structured questions.

        Args:
            content: JSON file content

        Returns:
            List of question dictionaries
        """
        questions = []

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return questions

        for section in data.get('sections', []):
            section_name = section.get('name', 'Unknown Section')

            for subsection in section.get('subsections', []):
                subsection_name = subsection.get('name', 'Unknown Subsection')
                question_number = 0

                for q in subsection.get('questions', []):
                    question_number += 1

                    question_text = q.get('question', '').strip()
                    answer_text = q.get('answer', '').strip()

                    if not question_text or not answer_text:
                        logger.warning(f"Skipping incomplete question in {section_name}/{subsection_name}")
                        continue

                    questions.append({
                        'section': section_name,
                        'subsection': subsection_name,
                        'question_number': question_number,
                        'question_text': question_text,
                        'answer_text': answer_text,
                        'difficulty': q.get('difficulty'),
                        'tags': ','.join(q.get('tags', []))
                    })

        logger.info(f"Parsed {len(questions)} questions from JSON")
        return questions

    def import_to_db(self, db: DatabaseManager, material_id: str, data: Any) -> int:
        """
        Import questions from JSON data into database.

        Args:
            db: DatabaseManager instance
            material_id: Material ID to associate questions with
            data: JSON data (dict) or file path (Path)

        Returns:
            Number of questions imported
        """
        logger.info(f"Importing JSON as material {material_id}")

        # Handle file path or raw data
        if isinstance(data, (str, Path)):
            with open(data, 'r', encoding='utf-8') as f:
                content = f.read()
        elif isinstance(data, dict):
            content = json.dumps(data)
        else:
            logger.error("Invalid data type for JSON import")
            return 0

        # Parse questions
        questions = self.parse_json(content)

        # Import to database
        count = 0
        for q in questions:
            try:
                db.execute(
                    """INSERT INTO questions (material_id, section, subsection, question_number,
                                             question_text, answer_text, difficulty, tags,
                                             created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        material_id,
                        q['section'],
                        q['subsection'],
                        q['question_number'],
                        q['question_text'],
                        q['answer_text'],
                        q.get('difficulty'),
                        q.get('tags'),
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    )
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to import question: {e}\nQuestion: {q}")

        logger.info(f"Imported {count} questions from JSON")
        return count
