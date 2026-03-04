"""Question parsing from markdown interview material."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from ..config.paths import get_questions_file


class QuestionParser:
    """Parses interview questions from markdown file."""

    def __init__(self, questions_file: Optional[Path] = None):
        """
        Initialize question parser.

        Args:
            questions_file: Path to questions markdown file. Uses default if None.
        """
        self.questions_file = questions_file or get_questions_file()
        self._content = None
        self._parsed_data = None

    def _load_content(self) -> str:
        """Load markdown content from file."""
        if self._content is None:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                self._content = f.read()
        return self._content

    def parse_all_questions(self) -> Dict[str, Any]:
        """
        Parse all questions from markdown file.

        Returns:
            Dictionary with structure:
            {
                'section_name': {
                    'subsections': {
                        'subsection_name': {
                            'questions': [
                                {
                                    'number': 1,
                                    'question': 'Question text',
                                    'answer': 'Answer text',
                                    'fullText': 'Combined Q&A'
                                }
                            ]
                        }
                    }
                }
            }
        """
        if self._parsed_data is not None:
            return self._parsed_data

        content = self._load_content()
        parsed = {}

        # Split by main sections (## heading)
        sections = re.split(r'\n## ', content)

        for section_text in sections[1:]:  # Skip header
            lines = section_text.split('\n')
            section_name = lines[0].strip()

            # Skip non-content sections
            if section_name in ['Table of Contents'] or section_name.startswith('['):
                continue

            parsed[section_name] = {'subsections': {}}

            # Split by subsections (### heading)
            subsections = re.split(r'\n### ', section_text)

            for subsection_text in subsections[1:]:  # Skip section intro
                sub_lines = subsection_text.split('\n')
                subsection_name = sub_lines[0].strip()

                # Parse questions in this subsection
                questions = self._parse_questions_from_text('\n'.join(sub_lines[1:]))

                parsed[section_name]['subsections'][subsection_name] = {
                    'questions': questions
                }

        self._parsed_data = parsed
        return parsed

    def _parse_questions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse individual questions from text block.

        Args:
            text: Text containing questions

        Returns:
            List of question dictionaries
        """
        questions = []

        # Split by question markers
        question_blocks = re.split(r'\n\*\*Q:', text)

        question_number = 1
        for block in question_blocks[1:]:  # Skip text before first question
            # Extract question and answer
            parts = block.split('\n', 1)
            if len(parts) < 2:
                continue

            # Get question text (everything up to **)
            question_match = re.match(r'([^*]+)', parts[0])
            if not question_match:
                continue

            question_text = question_match.group(1).strip()

            # Get answer (rest of the block until next question or separator)
            answer_text = parts[1] if len(parts) > 1 else ""

            # Clean up answer - stop at --- separator or next section
            answer_text = re.split(r'\n---\n|\n## |\n### ', answer_text)[0].strip()

            questions.append({
                'number': question_number,
                'question': question_text,
                'answer': answer_text,
                'fullText': f"Q: {question_text}\n\n{answer_text}"
            })

            question_number += 1

        return questions

    def get_question(
        self,
        section: str,
        subsection: str,
        question_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific question by location.

        Args:
            section: Section name
            subsection: Subsection name
            question_number: Question number (1-indexed)

        Returns:
            Question dictionary or None if not found
        """
        parsed = self.parse_all_questions()

        if section not in parsed:
            return None

        if subsection not in parsed[section]['subsections']:
            return None

        questions = parsed[section]['subsections'][subsection]['questions']

        # Find question by number
        for q in questions:
            if q['number'] == question_number:
                return {
                    'section': section,
                    'subsection': subsection,
                    **q
                }

        return None

    def get_next_question(
        self,
        section: str,
        subsection: str,
        last_question_number: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Get the next question in a subsection.

        Args:
            section: Section name
            subsection: Subsection name
            last_question_number: Last question number answered (0 for first)

        Returns:
            Next question dictionary or None if no more questions
        """
        return self.get_question(section, subsection, last_question_number + 1)

    def get_all_questions_in_subsection(
        self,
        section: str,
        subsection: str
    ) -> List[Dict[str, Any]]:
        """
        Get all questions in a subsection.

        Args:
            section: Section name
            subsection: Subsection name

        Returns:
            List of question dictionaries
        """
        parsed = self.parse_all_questions()

        if section not in parsed:
            return []

        if subsection not in parsed[section]['subsections']:
            return []

        questions = parsed[section]['subsections'][subsection]['questions']

        # Add section/subsection info to each question
        return [
            {
                'section': section,
                'subsection': subsection,
                **q
            }
            for q in questions
        ]

    def get_sections(self) -> List[str]:
        """
        Get list of all section names.

        Returns:
            List of section names
        """
        parsed = self.parse_all_questions()
        return list(parsed.keys())

    def get_subsections(self, section: str) -> List[str]:
        """
        Get list of subsection names for a section.

        Args:
            section: Section name

        Returns:
            List of subsection names
        """
        parsed = self.parse_all_questions()

        if section not in parsed:
            return []

        return list(parsed[section]['subsections'].keys())

    def get_question_count(self, section: Optional[str] = None, subsection: Optional[str] = None) -> int:
        """
        Get count of questions.

        Args:
            section: Optional section to filter by
            subsection: Optional subsection to filter by (requires section)

        Returns:
            Number of questions
        """
        parsed = self.parse_all_questions()

        if section and subsection:
            if section in parsed and subsection in parsed[section]['subsections']:
                return len(parsed[section]['subsections'][subsection]['questions'])
            return 0

        if section:
            if section not in parsed:
                return 0
            total = 0
            for sub_data in parsed[section]['subsections'].values():
                total += len(sub_data['questions'])
            return total

        # Total across all sections
        total = 0
        for section_data in parsed.values():
            for sub_data in section_data['subsections'].values():
                total += len(sub_data['questions'])
        return total

    def search_questions(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search for questions containing a keyword.

        Args:
            keyword: Keyword to search for (case-insensitive)

        Returns:
            List of matching questions with location info
        """
        parsed = self.parse_all_questions()
        results = []
        keyword_lower = keyword.lower()

        for section_name, section_data in parsed.items():
            for subsection_name, subsection_data in section_data['subsections'].items():
                for question in subsection_data['questions']:
                    if (keyword_lower in question['question'].lower() or
                        keyword_lower in question['answer'].lower()):
                        results.append({
                            'section': section_name,
                            'subsection': subsection_name,
                            **question
                        })

        return results
