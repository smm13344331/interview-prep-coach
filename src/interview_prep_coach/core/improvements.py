"""Improvement logging for interview preparation material using database."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .database import DatabaseManager

logger = logging.getLogger(__name__)


class ImprovementLogger:
    """Manages improvement tracking for interview material in database."""

    def __init__(self, db: DatabaseManager):
        """
        Initialize improvement logger.

        Args:
            db: DatabaseManager instance
        """
        self.db = db
        logger.debug("ImprovementLogger initialized")

    def log_improvement(
        self,
        material_id: str,
        improvement_type: str,
        section: str,
        subsection: str,
        description: str,
        question_id: Optional[int] = None,
        priority: str = "medium",
        suggested_by: str = "user"
    ) -> int:
        """
        Log a new improvement.

        Args:
            material_id: Material ID
            improvement_type: Type of improvement (unclear_question, missing_topic, etc.)
            section: Section name
            subsection: Subsection name
            description: Detailed description of the improvement
            question_id: Specific question ID if applicable
            priority: Priority level (low, medium, high, critical)
            suggested_by: Who suggested it (user, system, coach)

        Returns:
            Improvement ID
        """
        try:
            cursor = self.db.execute(
                """INSERT INTO improvements (material_id, question_id, section, subsection,
                                            improvement_type, description, priority, status,
                                            suggested_by, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    material_id,
                    question_id,
                    section,
                    subsection,
                    improvement_type,
                    description,
                    priority,
                    'pending',
                    suggested_by,
                    datetime.now().isoformat()
                )
            )

            improvement_id = cursor.lastrowid
            logger.info(f"Logged improvement {improvement_id} for {section}/{subsection}")
            return improvement_id

        except Exception as e:
            logger.error(f"Failed to log improvement: {e}", exc_info=True)
            return 0

    def mark_implemented(
        self,
        improvement_id: int,
        notes: Optional[str] = None
    ) -> bool:
        """
        Mark an improvement as implemented.

        Args:
            improvement_id: Improvement ID
            notes: Notes about the implementation

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.db.execute(
                """UPDATE improvements
                   SET status = ?, implemented_at = ?, implementation_notes = ?
                   WHERE id = ?""",
                ('implemented', datetime.now().isoformat(), notes, improvement_id)
            )

            if result.rowcount == 0:
                logger.warning(f"Improvement {improvement_id} not found")
                return False

            logger.info(f"Marked improvement {improvement_id} as implemented")
            return True

        except Exception as e:
            logger.error(f"Failed to mark improvement as implemented: {e}", exc_info=True)
            return False

    def get_pending_improvements(
        self,
        material_id: Optional[str] = None,
        section: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending improvements, optionally filtered.

        Args:
            material_id: Filter by material ID
            section: Filter by section name
            priority: Filter by priority level

        Returns:
            List of pending improvements
        """
        query = "SELECT * FROM improvements WHERE status = 'pending'"
        params = []

        if material_id:
            query += " AND material_id = ?"
            params.append(material_id)

        if section:
            query += " AND section = ?"
            params.append(section)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        query += " ORDER BY created_at DESC"

        return self.db.fetchall(query, tuple(params))

    def get_implemented_improvements(
        self,
        material_id: Optional[str] = None,
        section: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get implemented improvements, optionally filtered.

        Args:
            material_id: Filter by material ID
            section: Filter by section name

        Returns:
            List of implemented improvements
        """
        query = "SELECT * FROM improvements WHERE status = 'implemented'"
        params = []

        if material_id:
            query += " AND material_id = ?"
            params.append(material_id)

        if section:
            query += " AND section = ?"
            params.append(section)

        query += " ORDER BY implemented_at DESC"

        return self.db.fetchall(query, tuple(params))

    def get_improvements_by_type(
        self,
        improvement_type: str,
        material_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get improvements by type.

        Args:
            improvement_type: Type of improvement
            material_id: Filter by material ID

        Returns:
            List of improvements
        """
        query = "SELECT * FROM improvements WHERE improvement_type = ?"
        params = [improvement_type]

        if material_id:
            query += " AND material_id = ?"
            params.append(material_id)

        query += " ORDER BY created_at DESC"

        return self.db.fetchall(query, tuple(params))

    def get_metrics(self, material_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get improvement metrics.

        Args:
            material_id: Filter by material ID

        Returns:
            Metrics dictionary
        """
        where_clause = "WHERE material_id = ?" if material_id else ""
        params = (material_id,) if material_id else ()

        # Total improvements
        total_result = self.db.fetchone(
            f"SELECT COUNT(*) as total FROM improvements {where_clause}",
            params
        )
        total = total_result['total'] or 0

        # Implemented improvements
        impl_result = self.db.fetchone(
            f"""SELECT COUNT(*) as implemented FROM improvements
                {where_clause}{"AND" if material_id else "WHERE"} status = 'implemented'""",
            params
        )
        implemented = impl_result['implemented'] or 0

        # Pending improvements
        pending = total - implemented

        # By type
        by_type_results = self.db.fetchall(
            f"""SELECT improvement_type, COUNT(*) as count
                FROM improvements {where_clause}
                GROUP BY improvement_type
                ORDER BY count DESC""",
            params
        )
        by_type = {row['improvement_type']: row['count'] for row in by_type_results}

        # By priority
        by_priority_results = self.db.fetchall(
            f"""SELECT priority, COUNT(*) as count
                FROM improvements {where_clause}
                GROUP BY priority
                ORDER BY
                    CASE priority
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END""",
            params
        )
        by_priority = {row['priority']: row['count'] for row in by_priority_results}

        # By suggested_by
        by_source_results = self.db.fetchall(
            f"""SELECT suggested_by, COUNT(*) as count
                FROM improvements {where_clause}
                GROUP BY suggested_by""",
            params
        )
        by_source = {row['suggested_by']: row['count'] for row in by_source_results}

        return {
            'totalImprovementsLogged': total,
            'totalImplemented': implemented,
            'totalPending': pending,
            'implementationRate': round(implemented / total, 2) if total > 0 else 0.0,
            'byType': by_type,
            'byPriority': by_priority,
            'bySource': by_source,
            'userSuggestions': by_source.get('user', 0),
            'systemIdentified': by_source.get('system', 0) + by_source.get('coach', 0)
        }
