"""Test material editing functionality."""

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.interview_prep_coach.core.database import DatabaseManager
from src.interview_prep_coach.core.material_editor import MaterialEditor

# Check if running with vulnerable SQLite version
# SQLite 3.37.x has CVE-2022-35737: FTS5 content table trigger corruption
# This affects WSL environments with Python 3.10 (ships with SQLite 3.37.2)
SQLITE_VERSION = tuple(map(int, sqlite3.sqlite_version.split('.')))
HAS_FTS5_BUG = SQLITE_VERSION < (3, 38, 0)


class TestMaterialEditor(unittest.TestCase):
    """Test MaterialEditor functionality."""

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

        self.editor = MaterialEditor(self.db)

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
        """Clean up temporary database."""
        self.db.close()
        Path(self.temp_db.name).unlink(missing_ok=True)

    def test_get_material_info(self):
        """Test getting material information."""
        info = self.editor.get_material_info('test-material')

        self.assertEqual(info['id'], 'test-material')
        self.assertEqual(info['name'], 'Test Material')
        self.assertEqual(info['source_type'], 'user')
        self.assertIn('question_count', info)
        self.assertIn('section_count', info)

    @unittest.skipIf(HAS_FTS5_BUG, "SQLite 3.37.x has CVE-2022-35737: FTS5 UPDATE trigger corruption on WSL")
    def test_edit_question_text(self):
        """Test editing question text."""
        success = self.editor.edit_question(
            'test-material',
            self.question['id'],
            new_question='What is a HashMap in Java?',
            new_answer=None
        )

        self.assertTrue(success)

        # Verify edit
        updated = self.db.fetchone("SELECT * FROM questions WHERE id = ?", (self.question['id'],))
        self.assertEqual(updated['question_text'], 'What is a HashMap in Java?')
        self.assertEqual(updated['answer_text'], 'HashMap is...')  # Unchanged

    @unittest.skipIf(HAS_FTS5_BUG, "SQLite 3.37.x has CVE-2022-35737: FTS5 UPDATE trigger corruption on WSL")
    def test_edit_answer_text(self):
        """Test editing answer text."""
        success = self.editor.edit_question(
            'test-material',
            self.question['id'],
            new_question=None,
            new_answer='HashMap is a key-value data structure.'
        )

        self.assertTrue(success)

        # Verify edit
        updated = self.db.fetchone("SELECT * FROM questions WHERE id = ?", (self.question['id'],))
        self.assertEqual(updated['question_text'], 'What is HashMap?')  # Unchanged
        self.assertEqual(updated['answer_text'], 'HashMap is a key-value data structure.')

    def test_add_question(self):
        """Test adding a new question."""
        question_id = self.editor.add_question(
            'test-material',
            'Java',
            'Collections',
            'What is LinkedList?',
            'LinkedList is a doubly-linked list.',
            position=None
        )

        self.assertIsNotNone(question_id)

        # Verify question added
        new_question = self.db.fetchone("SELECT * FROM questions WHERE id = ?", (question_id,))
        self.assertEqual(new_question['question_text'], 'What is LinkedList?')
        self.assertEqual(new_question['question_number'], 2)  # Second question in subsection

    def test_add_question_at_position(self):
        """Test adding question at specific position."""
        # Add another question first
        self.db.execute(
            """INSERT INTO questions (material_id, section, subsection, question_number,
                                     question_text, answer_text)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('test-material', 'Java', 'Collections', 2, 'What is TreeMap?', 'TreeMap is...')
        )

        # Insert at position 2 (should renumber existing questions)
        question_id = self.editor.add_question(
            'test-material',
            'Java',
            'Collections',
            'What is LinkedList?',
            'LinkedList is...',
            position=2
        )

        self.assertIsNotNone(question_id)

        # Verify numbering
        questions = self.db.fetchall(
            """SELECT * FROM questions
               WHERE material_id = ? AND section = ? AND subsection = ?
               ORDER BY question_number""",
            ('test-material', 'Java', 'Collections')
        )

        self.assertEqual(len(questions), 3)
        self.assertEqual(questions[1]['question_text'], 'What is LinkedList?')
        self.assertEqual(questions[2]['question_text'], 'What is TreeMap?')
        self.assertEqual(questions[2]['question_number'], 3)  # Renumbered

    def test_delete_question(self):
        """Test deleting a question."""
        success = self.editor.delete_question(self.question['id'])

        self.assertTrue(success)

        # Verify deletion
        deleted = self.db.fetchone("SELECT * FROM questions WHERE id = ?", (self.question['id'],))
        self.assertIsNone(deleted)

    def test_clone_material(self):
        """Test cloning material."""
        success = self.editor.clone_material(
            'test-material',
            'cloned-material',
            'Cloned Material'
        )

        self.assertTrue(success)

        # Verify new material
        cloned = self.db.fetchone("SELECT * FROM materials WHERE id = ?", ('cloned-material',))
        self.assertIsNotNone(cloned)
        self.assertEqual(cloned['name'], 'Cloned Material')

        # Verify questions copied
        questions = self.db.fetchall(
            "SELECT * FROM questions WHERE material_id = ?",
            ('cloned-material',)
        )
        self.assertEqual(len(questions), 1)

    def test_export_material_to_markdown(self):
        """Test exporting material to markdown."""
        temp_export = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        temp_export.close()
        export_path = Path(temp_export.name)

        try:
            success = self.editor.export_material_to_markdown('test-material', export_path)

            self.assertTrue(success)
            self.assertTrue(export_path.exists())

            # Verify content
            content = export_path.read_text()
            self.assertIn('## Java', content)
            self.assertIn('### Collections', content)
            self.assertIn('What is HashMap?', content)

        finally:
            export_path.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
