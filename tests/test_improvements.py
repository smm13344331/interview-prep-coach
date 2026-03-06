"""Test improvement logging functionality."""

import tempfile
import unittest
from pathlib import Path

from src.interview_prep_coach.core.database import DatabaseManager
from src.interview_prep_coach.core.improvements import ImprovementLogger


class TestImprovementLogger(unittest.TestCase):
    """Test ImprovementLogger functionality."""

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

        self.logger = ImprovementLogger(self.db)

        # Create test material
        self.db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('test-material', 'Test Material', 'Test', '1.0.0', 'user', True)
        )

    def tearDown(self):
        """Clean up."""
        self.db.close()
        Path(self.temp_db.name).unlink(missing_ok=True)

    def test_log_improvement(self):
        """Test logging an improvement."""
        improvement_id = self.logger.log_improvement(
            'test-material',
            'unclear_question',
            'Java',
            'Collections',
            'Question is ambiguous',
            None,
            'high',
            'user'
        )

        self.assertIsNotNone(improvement_id)
        self.assertGreater(improvement_id, 0)

        # Verify improvement logged
        improvement = self.db.fetchone(
            "SELECT * FROM improvements WHERE id = ?",
            (improvement_id,)
        )
        self.assertEqual(improvement['improvement_type'], 'unclear_question')
        self.assertEqual(improvement['priority'], 'high')
        self.assertEqual(improvement['status'], 'pending')

    def test_get_pending_improvements(self):
        """Test getting pending improvements."""
        # Log some improvements
        self.logger.log_improvement(
            'test-material', 'unclear_question', 'Java', 'Collections',
            'Fix question 1', None, 'high', 'user'
        )
        self.logger.log_improvement(
            'test-material', 'missing_topic', 'Spring', 'Core',
            'Add question about DI', None, 'medium', 'coach'
        )

        pending = self.logger.get_pending_improvements('test-material')

        self.assertEqual(len(pending), 2)
        self.assertEqual(pending[0]['status'], 'pending')

    def test_get_pending_improvements_filtered(self):
        """Test filtering pending improvements."""
        # Log improvements
        self.logger.log_improvement(
            'test-material', 'unclear_question', 'Java', 'Collections',
            'Fix question 1', None, 'high', 'user'
        )
        self.logger.log_improvement(
            'test-material', 'missing_topic', 'Spring', 'Core',
            'Add question', None, 'low', 'coach'
        )

        # Filter by section
        pending = self.logger.get_pending_improvements('test-material', section='Java')
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['section'], 'Java')

        # Filter by priority
        pending = self.logger.get_pending_improvements('test-material', priority='high')
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['priority'], 'high')

    def test_mark_implemented(self):
        """Test marking improvement as implemented."""
        improvement_id = self.logger.log_improvement(
            'test-material', 'unclear_question', 'Java', 'Collections',
            'Fix question', None, 'high', 'user'
        )

        success = self.logger.mark_implemented(improvement_id, 'Question updated')

        self.assertTrue(success)

        # Verify status changed
        improvement = self.db.fetchone(
            "SELECT * FROM improvements WHERE id = ?",
            (improvement_id,)
        )
        self.assertEqual(improvement['status'], 'implemented')
        self.assertIsNotNone(improvement['implemented_at'])
        self.assertEqual(improvement['implementation_notes'], 'Question updated')

    def test_get_implemented_improvements(self):
        """Test getting implemented improvements."""
        # Log and implement
        id1 = self.logger.log_improvement(
            'test-material', 'unclear_question', 'Java', 'Collections',
            'Fix question', None, 'high', 'user'
        )
        self.logger.mark_implemented(id1, 'Done')

        # Log another (keep pending)
        self.logger.log_improvement(
            'test-material', 'missing_topic', 'Spring', 'Core',
            'Add question', None, 'medium', 'coach'
        )

        implemented = self.logger.get_implemented_improvements('test-material')

        self.assertEqual(len(implemented), 1)
        self.assertEqual(implemented[0]['status'], 'implemented')

    def test_get_metrics(self):
        """Test getting improvement metrics."""
        # Log improvements
        self.logger.log_improvement(
            'test-material', 'unclear_question', 'Java', 'Collections',
            'Fix', None, 'high', 'user'
        )
        id2 = self.logger.log_improvement(
            'test-material', 'missing_topic', 'Spring', 'Core',
            'Add', None, 'medium', 'coach'
        )
        self.logger.mark_implemented(id2, 'Done')

        metrics = self.logger.get_metrics('test-material')

        self.assertEqual(metrics['totalImprovementsLogged'], 2)
        self.assertEqual(metrics['totalPending'], 1)
        self.assertEqual(metrics['totalImplemented'], 1)
        self.assertIn('unclear_question', metrics['byType'])
        self.assertIn('missing_topic', metrics['byType'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
