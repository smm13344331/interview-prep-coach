"""Test progress tracking functionality."""

import tempfile
import unittest
from pathlib import Path

from src.interview_prep_coach.core.database import DatabaseManager
from src.interview_prep_coach.core.progress import ProgressTracker


class TestProgressTracker(unittest.TestCase):
    """Test ProgressTracker functionality."""

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

        self.tracker = ProgressTracker(self.db)

        # Create test material and question
        self.db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('test-material', 'Test Material', 'Test', '1.0.0', 'user', True)
        )

        self.db.execute(
            """INSERT INTO questions (material_id, section, subsection, question_number,
                                     question_text, answer_text)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('test-material', 'Java', 'Collections', 1, 'What is HashMap?', 'HashMap is...')
        )

        self.question = self.db.fetchone(
            "SELECT * FROM questions WHERE material_id = ?",
            ('test-material',)
        )

    def tearDown(self):
        """Clean up."""
        self.db.close()
        Path(self.temp_db.name).unlink(missing_ok=True)

    def test_start_session(self):
        """Test starting a session."""
        session_id = self.tracker.start_session('test-material')

        self.assertIsNotNone(session_id)
        self.assertGreater(session_id, 0)

        # Verify session exists
        session = self.db.fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
        self.assertIsNotNone(session)
        self.assertEqual(session['material_id'], 'test-material')

    def test_end_session(self):
        """Test ending a session."""
        session_id = self.tracker.start_session('test-material')

        success = self.tracker.end_session(session_id)
        self.assertTrue(success)

        # Verify session is ended
        session = self.db.fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
        self.assertIsNotNone(session['ended_at'])

    def test_update_progress_correct(self):
        """Test updating progress with correct answer."""
        success = self.tracker.update_progress(
            'test-material',
            self.question['id'],
            'correct',
            None,
            'Good answer'
        )

        self.assertTrue(success)

        # Verify progress entry
        progress = self.db.fetchall(
            "SELECT * FROM progress WHERE question_id = ?",
            (self.question['id'],)
        )
        self.assertEqual(len(progress), 1)
        self.assertEqual(progress[0]['response'], 'correct')
        self.assertEqual(progress[0]['notes'], 'Good answer')

    def test_update_progress_multiple_attempts(self):
        """Test multiple attempts on same question."""
        # First attempt - incorrect
        self.tracker.update_progress('test-material', self.question['id'], 'incorrect')

        # Second attempt - correct
        self.tracker.update_progress('test-material', self.question['id'], 'correct')

        # Verify both attempts recorded
        attempts = self.db.fetchall(
            "SELECT * FROM progress WHERE question_id = ? ORDER BY attempt_number",
            (self.question['id'],)
        )
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0]['attempt_number'], 1)
        self.assertEqual(attempts[1]['attempt_number'], 2)

    def test_get_statistics(self):
        """Test getting statistics."""
        # Add some progress
        self.tracker.update_progress('test-material', self.question['id'], 'correct')

        stats = self.tracker.get_statistics('test-material')

        self.assertIn('overallProgress', stats)
        self.assertEqual(stats['overallProgress']['totalQuestionsAsked'], 1)
        self.assertEqual(stats['overallProgress']['totalQuestionsCorrect'], 1)
        self.assertEqual(stats['overallProgress']['accuracy'], 1.0)

    def test_get_weak_areas(self):
        """Test identifying weak areas."""
        # Add more questions
        for i in range(2, 6):
            self.db.execute(
                """INSERT INTO questions (material_id, section, subsection, question_number,
                                         question_text, answer_text)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ('test-material', 'Java', 'Collections', i, f'Question {i}?', f'Answer {i}')
            )

        questions = self.db.fetchall(
            "SELECT * FROM questions WHERE material_id = ?",
            ('test-material',)
        )

        # Answer some correctly, some incorrectly
        self.tracker.update_progress('test-material', questions[0]['id'], 'correct')
        self.tracker.update_progress('test-material', questions[1]['id'], 'incorrect')
        self.tracker.update_progress('test-material', questions[2]['id'], 'incorrect')
        self.tracker.update_progress('test-material', questions[3]['id'], 'incorrect')

        weak_areas = self.tracker.get_weak_areas('test-material', threshold=0.6)

        # Collections should be weak (25% correct)
        self.assertGreater(len(weak_areas), 0)
        self.assertEqual(weak_areas[0]['subsection'], 'Collections')
        self.assertLess(weak_areas[0]['accuracy'], 0.6)

    def test_reset_progress(self):
        """Test resetting progress."""
        # Add progress
        self.tracker.update_progress('test-material', self.question['id'], 'correct')

        # Reset
        self.tracker.reset_progress('test-material')

        # Verify progress deleted
        progress = self.db.fetchall(
            "SELECT * FROM progress WHERE material_id = ?",
            ('test-material',)
        )
        self.assertEqual(len(progress), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
