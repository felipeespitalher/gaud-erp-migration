"""Abstract base class for backup parsers."""
from abc import ABC, abstractmethod
from typing import Optional, List

from src.schema.models import SourceSchema


class DatabaseBackupParser(ABC):
    """Abstract base class for database backup parsers."""

    @abstractmethod
    def parse(
        self,
        content: str,
        selected_tables: Optional[List[str]] = None,
    ) -> SourceSchema:
        """
        Parse backup content and return schema.

        Args:
            content: Raw backup content (SQL, CSV, etc.)
            selected_tables: Optional list of table names to include.
                            If None, parse all tables.

        Returns:
            SourceSchema: Parsed schema

        Raises:
            ParseException: If parsing fails
        """
        pass

    @staticmethod
    def detect_format(file_path: str) -> str:
        """Detect file format from extension."""
        ext = file_path.lower().split('.')[-1]
        return ext
