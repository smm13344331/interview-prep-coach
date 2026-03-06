"""Test bundled material import compatibility."""

import tempfile
import unittest
from pathlib import Path

from src.interview_prep_coach.core.database import DatabaseManager
from src.interview_prep_coach.plugins.bundled import JavaSpringPlugin


class TestBundledMaterialImport(unittest.TestCase):
    """Test that bundled material imports correctly."""

    def setUp(self):
        """Create temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db = DatabaseManager(Path(self.temp_db.name))

        # Load schema from source (not installed package)
        schema_path = Path(__file__).parent.parent / 'src' / 'interview_prep_coach' / 'data' / 'schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        self.db.get_connection().executescript(schema_sql)

    def tearDown(self):
        """Clean up temporary database."""
        self.db.close()
        Path(self.temp_db.name).unlink(missing_ok=True)

    def test_plugin_metadata(self):
        """Test plugin has correct metadata."""
        plugin = JavaSpringPlugin()

        self.assertEqual(plugin.plugin_id, "java-spring-bundled")
        self.assertIsNotNone(plugin.name)
        self.assertIsNotNone(plugin.description)
        self.assertIsNotNone(plugin.version)

    def test_import_bundled_material(self):
        """Test importing bundled Java/Spring material."""
        plugin = JavaSpringPlugin()

        # Register material
        self.db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (plugin.plugin_id, plugin.name, plugin.description,
             plugin.version, 'bundled', True)
        )

        # Import questions
        success = plugin.import_material(self.db, plugin.plugin_id)

        self.assertTrue(success, "Import should succeed")

    def test_imported_question_count(self):
        """Test that expected number of questions are imported."""
        plugin = JavaSpringPlugin()

        # Register and import
        self.db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (plugin.plugin_id, plugin.name, plugin.description,
             plugin.version, 'bundled', True)
        )
        plugin.import_material(self.db, plugin.plugin_id)

        # Count questions
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM questions WHERE material_id = ?",
            (plugin.plugin_id,)
        )

        question_count = result['count']

        # Should have at least 100 questions (adjust based on actual content)
        self.assertGreater(question_count, 100,
                          f"Should import at least 100 questions, got {question_count}")

        print(f"\n✅ Imported {question_count} questions")

    def test_section_structure(self):
        """Test that sections and subsections are correctly imported."""
        plugin = JavaSpringPlugin()

        # Register and import
        self.db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (plugin.plugin_id, plugin.name, plugin.description,
             plugin.version, 'bundled', True)
        )
        plugin.import_material(self.db, plugin.plugin_id)

        # Get sections
        sections = self.db.fetchall(
            "SELECT DISTINCT section FROM questions WHERE material_id = ? ORDER BY section",
            (plugin.plugin_id,)
        )

        section_names = [s['section'] for s in sections]

        # Verify expected sections exist
        expected_sections = [
            "Java Core Concepts",
            "Spring Framework",
            "Database Concepts",
            "Docker",
            "Kubernetes",
            "System Design Questions"
        ]

        for expected in expected_sections:
            self.assertIn(expected, section_names,
                         f"Expected section '{expected}' not found")

        print(f"\n✅ Found {len(sections)} sections:")
        for section in sections:
            subsection_count = self.db.fetchone(
                """SELECT COUNT(DISTINCT subsection) as count
                   FROM questions
                   WHERE material_id = ? AND section = ?""",
                (plugin.plugin_id, section['section'])
            )
            print(f"   📁 {section['section']} ({subsection_count['count']} subsections)")

    def test_all_questions_have_subsections(self):
        """Test that all questions have proper subsection headers."""
        plugin = JavaSpringPlugin()

        # Register and import
        self.db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (plugin.plugin_id, plugin.name, plugin.description,
             plugin.version, 'bundled', True)
        )
        plugin.import_material(self.db, plugin.plugin_id)

        # Check for questions without subsections
        questions_without_subsections = self.db.fetchall(
            """SELECT section, subsection, COUNT(*) as count
               FROM questions
               WHERE material_id = ? AND (subsection IS NULL OR subsection = '')
               GROUP BY section, subsection""",
            (plugin.plugin_id,)
        )

        if questions_without_subsections:
            print("\n⚠️  Questions without subsections:")
            for q in questions_without_subsections:
                print(f"   Section: {q['section']}, Count: {q['count']}")

        # All questions should have subsections
        self.assertEqual(len(questions_without_subsections), 0,
                        "All questions should have subsection headers")

    def test_question_text_format(self):
        """Test that questions have proper text and answers."""
        plugin = JavaSpringPlugin()

        # Register and import
        self.db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (plugin.plugin_id, plugin.name, plugin.description,
             plugin.version, 'bundled', True)
        )
        plugin.import_material(self.db, plugin.plugin_id)

        # Get a sample question
        question = self.db.fetchone(
            "SELECT * FROM questions WHERE material_id = ? LIMIT 1",
            (plugin.plugin_id,)
        )

        self.assertIsNotNone(question)
        self.assertIsNotNone(question['question_text'])
        self.assertIsNotNone(question['answer_text'])
        self.assertGreater(len(question['question_text']), 10)
        self.assertGreater(len(question['answer_text']), 10)

        print(f"\n✅ Sample question verified:")
        print(f"   Section: {question['section']}")
        print(f"   Subsection: {question['subsection']}")
        print(f"   Question: {question['question_text'][:80]}...")


if __name__ == '__main__':
    unittest.main(verbosity=2)
