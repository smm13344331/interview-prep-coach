"""Plugin management for material sources."""

import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from .database import DatabaseManager
from ..plugins.base import MaterialPlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages material source plugins.

    Handles plugin registration, enabling/disabling, and lifecycle management.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize plugin manager.

        Args:
            db: DatabaseManager instance
        """
        self.db = db
        logger.debug("PluginManager initialized")

    def list_plugins(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all registered plugins.

        Args:
            enabled_only: If True, only return enabled plugins

        Returns:
            List of plugin dictionaries
        """
        query = "SELECT * FROM plugins"
        if enabled_only:
            query += " WHERE is_enabled = TRUE"
        query += " ORDER BY name"

        plugins = self.db.fetchall(query)

        # Parse JSON fields
        for plugin in plugins:
            if plugin.get('config'):
                try:
                    plugin['config'] = json.loads(plugin['config'])
                except json.JSONDecodeError:
                    plugin['config'] = {}

            if plugin.get('metadata'):
                try:
                    plugin['metadata'] = json.loads(plugin['metadata'])
                except json.JSONDecodeError:
                    plugin['metadata'] = {}

        return plugins

    def install_plugin(self, plugin_id: str, plugin: MaterialPlugin, config: Optional[Dict] = None) -> bool:
        """
        Install and register a plugin.

        Args:
            plugin_id: Unique plugin identifier
            plugin: MaterialPlugin instance
            config: Optional plugin configuration

        Returns:
            True if installation successful, False otherwise
        """
        try:
            logger.info(f"Installing plugin: {plugin_id}")

            # Check if already installed
            existing = self.get_plugin_info(plugin_id)
            if existing:
                logger.warning(f"Plugin {plugin_id} already installed")
                return False

            # Get plugin metadata
            metadata = plugin.get_metadata()

            # Register plugin
            self.db.execute(
                """INSERT INTO plugins (id, name, version, description, plugin_type,
                                       config, is_enabled, installed_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    plugin_id,
                    plugin.name,
                    plugin.version,
                    plugin.description,
                    'material_source',
                    json.dumps(config or {}),
                    True,
                    datetime.now().isoformat(),
                    json.dumps(metadata)
                )
            )

            logger.info(f"Plugin {plugin_id} installed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to install plugin {plugin_id}: {e}", exc_info=True)
            return False

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """
        Uninstall a plugin.

        Note: This removes the plugin registration but does not delete
        associated material or data.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if uninstallation successful, False otherwise
        """
        try:
            logger.info(f"Uninstalling plugin: {plugin_id}")

            # Check if plugin exists
            if not self.get_plugin_info(plugin_id):
                logger.warning(f"Plugin {plugin_id} not found")
                return False

            # Remove plugin
            self.db.execute("DELETE FROM plugins WHERE id = ?", (plugin_id,))

            logger.info(f"Plugin {plugin_id} uninstalled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to uninstall plugin {plugin_id}: {e}", exc_info=True)
            return False

    def enable_plugin(self, plugin_id: str) -> bool:
        """
        Enable a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.db.execute(
                "UPDATE plugins SET is_enabled = TRUE WHERE id = ?",
                (plugin_id,)
            )

            if result.rowcount == 0:
                logger.warning(f"Plugin {plugin_id} not found")
                return False

            logger.info(f"Plugin {plugin_id} enabled")
            return True

        except Exception as e:
            logger.error(f"Failed to enable plugin {plugin_id}: {e}", exc_info=True)
            return False

    def disable_plugin(self, plugin_id: str) -> bool:
        """
        Disable a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.db.execute(
                "UPDATE plugins SET is_enabled = FALSE WHERE id = ?",
                (plugin_id,)
            )

            if result.rowcount == 0:
                logger.warning(f"Plugin {plugin_id} not found")
                return False

            logger.info(f"Plugin {plugin_id} disabled")
            return True

        except Exception as e:
            logger.error(f"Failed to disable plugin {plugin_id}: {e}", exc_info=True)
            return False

    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Plugin dictionary or None if not found
        """
        plugin = self.db.fetchone(
            "SELECT * FROM plugins WHERE id = ?",
            (plugin_id,)
        )

        if not plugin:
            return None

        # Parse JSON fields
        if plugin.get('config'):
            try:
                plugin['config'] = json.loads(plugin['config'])
            except json.JSONDecodeError:
                plugin['config'] = {}

        if plugin.get('metadata'):
            try:
                plugin['metadata'] = json.loads(plugin['metadata'])
            except json.JSONDecodeError:
                plugin['metadata'] = {}

        return plugin

    def load_plugin(self, plugin_id: str) -> Optional[MaterialPlugin]:
        """
        Load a plugin instance.

        Note: This is a simplified implementation for bundled plugins.
        Future versions could support dynamic loading.

        Args:
            plugin_id: Plugin identifier

        Returns:
            MaterialPlugin instance or None if not found
        """
        from ..plugins.bundled import JavaSpringPlugin

        # Map plugin IDs to classes
        plugin_classes = {
            'java-spring-bundled': JavaSpringPlugin,
        }

        plugin_class = plugin_classes.get(plugin_id)
        if plugin_class:
            return plugin_class()

        logger.warning(f"Plugin {plugin_id} not found in registry")
        return None

    def update_last_used(self, plugin_id: str) -> None:
        """
        Update last used timestamp for a plugin.

        Args:
            plugin_id: Plugin identifier
        """
        self.db.execute(
            "UPDATE plugins SET last_used_at = ? WHERE id = ?",
            (datetime.now().isoformat(), plugin_id)
        )
