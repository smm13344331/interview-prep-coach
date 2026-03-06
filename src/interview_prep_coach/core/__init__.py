"""Core functionality for interview prep coach."""

from .progress import ProgressTracker
from .improvements import ImprovementLogger
from .questions import QuestionParser
from .material_editor import MaterialEditor
from .database import DatabaseManager
from .plugin_manager import PluginManager
from .schema import CURRENT_SCHEMA_VERSION, get_schema_sql

__all__ = [
    "ProgressTracker",
    "ImprovementLogger",
    "QuestionParser",
    "MaterialEditor",
    "DatabaseManager",
    "PluginManager",
    "CURRENT_SCHEMA_VERSION",
    "get_schema_sql",
]
