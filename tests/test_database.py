"""Test database operations."""

import tempfile
import unittest
from pathlib import Path

from src.interview_prep_coach.core.database import DatabaseManager
from src.interview_prep_coach.core.schema import CURRENT_SCHEMA_VERSION, get_table_list


class TestDatabaseManager(unittest.TestCase):
    """Test DatabaseManager functionality."""

    def setUp(self):
        """Create temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db = DatabaseManager(Path(self.temp_db.name))

    def tearDown(self):
        """Clean up temporary database."""
        self.db.close()
        Path(self.temp_db.name).unlink(missing_ok=True)

    def test_initialize_schema(self):
        """Test schema initialization."""
        # Load schema from source
        schema_path = Path(__file__).parent.parent / 'src' / 'interview_prep_coach' / 'data' / 'schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        self.db.get_connection().executescript(schema_sql)

        # Check schema version
        version = self.db.get_schema_version()
        self.assertEqual(version, CURRENT_SCHEMA_VERSION)

    def test_all_tables_created(self):
        """Test that all tables are created."""
        schema_path = Path(__file__).parent.parent / 'src' / 'interview_prep_coach' / 'data' / 'schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        self.db.get_connection().executescript(schema_sql)

        expected_tables = get_table_list()

        # Query actual tables
        tables = self.db.fetchall(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = [t['name'] for t in tables]

        for expected in expected_tables:
            self.assertIn(expected, table_names, f"Table {expected} not created")

    def test_foreign_keys_enabled(self):
        """Test that foreign keys are enabled."""
        schema_path = Path(__file__).parent.parent / 'src' / 'interview_prep_coach' / 'data' / 'schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        self.db.get_connection().executescript(schema_sql)

        result = self.db.fetchone("PRAGMA foreign_keys")
        self.assertEqual(result['foreign_keys'], 1, "Foreign keys should be enabled")

    def test_execute_insert(self):
        """Test INSERT operation."""
        schema_path = Path(__file__).parent.parent / 'src' / 'interview_prep_coach' / 'data' / 'schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        self.db.get_connection().executescript(schema_sql)

        self.db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('test-material', 'Test Material', 'Test description', '1.0.0', 'user', True)
        )

        material = self.db.fetchone("SELECT * FROM materials WHERE id = ?", ('test-material',))
        self.assertIsNotNone(material)
        self.assertEqual(material['name'], 'Test Material')

    def test_fetchall(self):
        """Test fetchall operation."""
        schema_path = Path(__file__).parent.parent / 'src' / 'interview_prep_coach' / 'data' / 'schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        self.db.get_connection().executescript(schema_sql)

        # Insert multiple records
        for i in range(3):
            self.db.execute(
                """INSERT INTO materials (id, name, description, version, source_type, is_active)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (f'material-{i}', f'Material {i}', 'Description', '1.0.0', 'user', False)
            )

        materials = self.db.fetchall("SELECT * FROM materials ORDER BY id")
        self.assertEqual(len(materials), 3)
        self.assertEqual(materials[0]['id'], 'material-0')

    def test_fetchone(self):
        """Test fetchone operation."""
        schema_path = Path(__file__).parent.parent / 'src' / 'interview_prep_coach' / 'data' / 'schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        self.db.get_connection().executescript(schema_sql)

        self.db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('material-1', 'Material 1', 'Description', '1.0.0', 'user', True)
        )

        material = self.db.fetchone("SELECT * FROM materials WHERE id = ?", ('material-1',))
        self.assertIsNotNone(material)
        self.assertEqual(material['name'], 'Material 1')

    def test_count_records(self):
        """Test record counting."""
        schema_path = Path(__file__).parent.parent / 'src' / 'interview_prep_coach' / 'data' / 'schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        self.db.get_connection().executescript(schema_sql)

        # Insert records
        for i in range(5):
            self.db.execute(
                """INSERT INTO materials (id, name, description, version, source_type, is_active)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (f'material-{i}', f'Material {i}', 'Description', '1.0.0', 'user', False)
            )

        count = self.db.count_records("materials")
        self.assertEqual(count, 5)

        # Test with condition
        count_user = self.db.count_records("materials", "source_type = ?", ('user',))
        self.assertEqual(count_user, 5)

    def test_cascade_delete(self):
        """Test that CASCADE delete works."""
        schema_path = Path(__file__).parent.parent / 'src' / 'interview_prep_coach' / 'data' / 'schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        self.db.get_connection().executescript(schema_sql)

        # Insert material
        self.db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('test-material', 'Test', 'Description', '1.0.0', 'user', True)
        )

        # Insert question
        self.db.execute(
            """INSERT INTO questions (material_id, section, subsection, question_number,
                                     question_text, answer_text)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('test-material', 'Section 1', 'Subsection 1', 1, 'Question?', 'Answer.')
        )

        # Delete material
        self.db.execute("DELETE FROM materials WHERE id = ?", ('test-material',))

        # Questions should be deleted too (CASCADE)
        questions = self.db.fetchall("SELECT * FROM questions WHERE material_id = ?", ('test-material',))
        self.assertEqual(len(questions), 0, "Questions should be deleted with material (CASCADE)")

    def test_unique_constraint(self):
        """Test that unique constraints work."""
        schema_path = Path(__file__).parent.parent / 'src' / 'interview_prep_coach' / 'data' / 'schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        self.db.get_connection().executescript(schema_sql)

        # Insert material
        self.db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('test-material', 'Test', 'Description', '1.0.0', 'user', True)
        )

        # Insert question
        self.db.execute(
            """INSERT INTO questions (material_id, section, subsection, question_number,
                                     question_text, answer_text)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('test-material', 'Section 1', 'Subsection 1', 1, 'Question?', 'Answer.')
        )

        # Try to insert duplicate (same material, section, subsection, question_number)
        with self.assertRaises(Exception):
            self.db.execute(
                """INSERT INTO questions (material_id, section, subsection, question_number,
                                         question_text, answer_text)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ('test-material', 'Section 1', 'Subsection 1', 1, 'Different question?', 'Different answer.')
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
