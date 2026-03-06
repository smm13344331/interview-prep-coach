"""Bundled Java & Spring Framework plugin."""

import logging
from pathlib import Path

from ..base import MaterialPlugin
from ..importers import MarkdownImporter
from ...core.database import DatabaseManager
from ...config.paths import get_bundled_questions_file

logger = logging.getLogger(__name__)


class JavaSpringPlugin(MaterialPlugin):
    """
    Bundled plugin for Java & Spring Framework interview preparation.

    Imports the bundled markdown file with Java and Spring questions.
    """

    @property
    def plugin_id(self) -> str:
        return "java-spring-bundled"

    @property
    def name(self) -> str:
        return "Java & Spring Framework Interview Prep"

    @property
    def description(self) -> str:
        return "Comprehensive interview questions for Java and Spring Framework, covering core concepts, advanced features, and infrastructure topics"

    @property
    def version(self) -> str:
        return "1.0.0"

    def import_material(self, db: DatabaseManager, material_id: str) -> bool:
        """
        Import bundled Java/Spring questions into database.

        Args:
            db: DatabaseManager instance
            material_id: Material ID (should match plugin_id)

        Returns:
            True if import successful, False otherwise
        """
        try:
            logger.info(f"Importing bundled Java/Spring material as {material_id}")

            # Get bundled markdown file
            bundled_file = get_bundled_questions_file()

            if not bundled_file.exists():
                logger.error(f"Bundled file not found: {bundled_file}")
                return False

            # Import using markdown importer
            importer = MarkdownImporter()
            count = importer.import_to_db(db, material_id, bundled_file)

            logger.info(f"Successfully imported {count} questions from bundled material")
            return count > 0

        except Exception as e:
            logger.error(f"Failed to import bundled material: {e}", exc_info=True)
            return False
