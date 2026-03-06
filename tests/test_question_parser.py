"""Test question parsing functionality."""

import tempfile
import unittest
from pathlib import Path

from src.interview_prep_coach.core.database import DatabaseManager
from src.interview_prep_coach.core.questions import QuestionParser


class TestQuestionParser(unittest.TestCase):
    """Test QuestionParser functionality."""

    def setUp(self):
        """Create temporary database and setup."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db = DatabaseManager(Path(self.temp_db.name))

        # Load schema
        schema_path = Path(__file__).parent.parent / 'src' / 'interview_prep_coach' / 'data' / 'schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        self.db.get_connection().executescript(schema_sql)

        self.parser = QuestionParser(self.db)

        # Create test material and questions
        self.db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('test-material', 'Test Material', 'Test', '1.0.0', 'user', True)
        )

        # Add sample questions
        questions = [
            ('Java', 'Collections', 1, 'What is HashMap?', 'HashMap is a data structure...'),
            ('Java', 'Collections', 2, 'What is ArrayList?', 'ArrayList is a resizable array...'),
            ('Java', 'Concurrency', 1, 'What is synchronized?', 'synchronized keyword...'),
            ('Spring', 'Core', 1, 'What is IoC?', 'Inversion of Control...'),
        ]

        for section, subsection, num, q, a in questions:
            self.db.execute(
                """INSERT INTO questions (material_id, section, subsection, question_number,
                                         question_text, answer_text)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ('test-material', section, subsection, num, q, a)
            )

    def tearDown(self):
        """Clean up."""
        self.db.close()
        Path(self.temp_db.name).unlink(missing_ok=True)

    def test_get_sections(self):
        """Test getting list of sections."""
        sections = self.parser.get_sections('test-material')

        self.assertEqual(len(sections), 2)
        self.assertIn('Java', sections)
        self.assertIn('Spring', sections)

    def test_get_subsections(self):
        """Test getting subsections for a section."""
        subsections = self.parser.get_subsections('Java', 'test-material')

        self.assertEqual(len(subsections), 2)
        self.assertIn('Collections', subsections)
        self.assertIn('Concurrency', subsections)

    def test_get_question(self):
        """Test getting specific question."""
        question = self.parser.get_question('Java', 'Collections', 1, 'test-material')

        self.assertIsNotNone(question)
        self.assertEqual(question['section'], 'Java')
        self.assertEqual(question['subsection'], 'Collections')
        self.assertEqual(question['number'], 1)  # Mapped from question_number
        self.assertEqual(question['question'], 'What is HashMap?')  # Mapped from question_text

    def test_get_next_question(self):
        """Test getting next question in sequence."""
        # Get first question
        next_q = self.parser.get_next_question('Java', 'Collections', 0, 'test-material')

        self.assertIsNotNone(next_q)
        self.assertEqual(next_q['number'], 1)  # Mapped from question_number

        # Get second question
        next_q = self.parser.get_next_question('Java', 'Collections', 1, 'test-material')

        self.assertIsNotNone(next_q)
        self.assertEqual(next_q['number'], 2)

        # No more questions
        next_q = self.parser.get_next_question('Java', 'Collections', 2, 'test-material')

        self.assertIsNone(next_q)

    def test_get_all_questions_in_subsection(self):
        """Test getting all questions in a subsection."""
        questions = self.parser.get_all_questions_in_subsection('Java', 'Collections', 'test-material')

        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0]['number'], 1)  # Mapped from question_number
        self.assertEqual(questions[1]['number'], 2)

    def test_search_questions(self):
        """Test full-text search."""
        # Note: FTS needs to be manually populated in tests
        # Rebuild FTS index
        self.db.execute("INSERT INTO questions_fts(questions_fts) VALUES('rebuild')")

        # Search for "HashMap"
        results = self.parser.search_questions('HashMap', 'test-material')

        self.assertGreater(len(results), 0)
        self.assertIn('HashMap', results[0]['question'])  # Mapped from question_text

        # Search for "resizable"
        results = self.parser.search_questions('resizable', 'test-material')

        self.assertGreater(len(results), 0)
        self.assertIn('ArrayList', results[0]['question'])

    def test_get_question_count(self):
        """Test getting question counts."""
        # Total count
        count = self.parser.get_question_count(None, None, 'test-material')
        self.assertEqual(count, 4)

        # Section count
        count = self.parser.get_question_count('Java', None, 'test-material')
        self.assertEqual(count, 3)

        # Subsection count
        count = self.parser.get_question_count('Java', 'Collections', 'test-material')
        self.assertEqual(count, 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
