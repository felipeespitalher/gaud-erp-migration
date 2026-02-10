"""Factory for creating appropriate parser based on file type."""
from pathlib import Path
from typing import Optional, List

from src.parser.backup_parser import DatabaseBackupParser
from src.parser.sql_parser import SqlParser
from src.parser.dialect_detector import SqlDialectDetector
from src.schema.models import SourceSchema


class BackupParserFactory:
    """Factory for creating database parsers."""

    # Map extensions to parser types
    PARSERS = {
        'sql': 'sql',
        'dump': 'sql',
        'bak': 'sql',
        'csv': 'csv',
        'xlsx': 'excel',
        'xls': 'excel',
        'json': 'json',
    }

    @staticmethod
    def create_parser(file_path: str) -> DatabaseBackupParser:
        """
        Create parser based on file extension.

        Args:
            file_path: Path to backup file

        Returns:
            DatabaseBackupParser: Appropriate parser instance

        Raises:
            ValueError: If file format is not supported
        """
        file_path = str(file_path).lower()
        ext = file_path.split('.')[-1] if '.' in file_path else ''

        if ext in BackupParserFactory.PARSERS:
            parser_type = BackupParserFactory.PARSERS[ext]

            if parser_type == 'sql':
                return SqlParser()
            elif parser_type == 'csv':
                # TODO: Implement CsvParser in PHASE 2
                raise NotImplementedError("CSV parser coming in PHASE 2")
            elif parser_type == 'excel':
                # TODO: Implement ExcelParser in PHASE 2
                raise NotImplementedError("Excel parser coming in PHASE 2")
            elif parser_type == 'json':
                # TODO: Implement JsonParser in PHASE 2
                raise NotImplementedError("JSON parser coming in PHASE 2")

        raise ValueError(f"Unsupported backup format: {ext}")

    @staticmethod
    def detect_dialect_from_file(file_path: str) -> str:
        """
        Detect SQL dialect from file content.

        Args:
            file_path: Path to SQL dump file

        Returns:
            str: Dialect ('postgresql', 'mysql', 'oracle', 'firebird', 'unknown')
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read first 100KB to detect dialect
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            sample = f.read(102400)  # 100KB sample

        return SqlDialectDetector.detect(sample)

    @staticmethod
    def parse_backup(
        file_path: str,
        selected_tables: Optional[List[str]] = None,
    ) -> SourceSchema:
        """
        Convenience method to parse a backup file in one call.

        Args:
            file_path: Path to backup file
            selected_tables: Optional list of table names to include

        Returns:
            SourceSchema: Parsed schema
        """
        parser = BackupParserFactory.create_parser(file_path)

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        return parser.parse(content, selected_tables)
