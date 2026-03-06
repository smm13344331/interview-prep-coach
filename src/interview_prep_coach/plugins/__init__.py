"""Plugin system for interview prep coach material sources."""

from .base import MaterialPlugin
from .importers import MarkdownImporter, JSONImporter

__all__ = [
    "MaterialPlugin",
    "MarkdownImporter",
    "JSONImporter",
]
