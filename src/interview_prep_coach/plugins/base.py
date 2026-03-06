"""Base classes for material plugins."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from ..core.database import DatabaseManager


class MaterialPlugin(ABC):
    """
    Base class for material source plugins.

    Material plugins provide interview questions from various sources
    (bundled, files, APIs, etc.) and import them into the database.
    """

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """
        Unique identifier for this plugin.

        Returns:
            Plugin ID (e.g., 'java-spring-bundled', 'python-leetcode')
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable plugin name.

        Returns:
            Plugin name (e.g., 'Java & Spring Framework Interview Prep')
        """
        pass

    @property
    def description(self) -> str:
        """
        Plugin description.

        Returns:
            Description of what this plugin provides
        """
        return ""

    @property
    def version(self) -> str:
        """
        Plugin version.

        Returns:
            Version string (e.g., '1.0.0')
        """
        return "1.0.0"

    @abstractmethod
    def import_material(self, db: DatabaseManager, material_id: str) -> bool:
        """
        Import questions into database.

        Args:
            db: DatabaseManager instance
            material_id: Unique identifier for this material in the database

        Returns:
            True if import successful, False otherwise
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get plugin metadata.

        Returns:
            Dictionary with plugin information
        """
        return {
            'plugin_id': self.plugin_id,
            'name': self.name,
            'description': self.description,
            'version': self.version
        }
