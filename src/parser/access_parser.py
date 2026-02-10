"""Microsoft Access file parser (.mdb, .accdb)."""
from typing import Optional, List

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from src.parser.backup_parser import DatabaseBackupParser
from src.schema.models import SourceSchema, SourceTable, SourceColumn


class AccessParser(DatabaseBackupParser):
    """Parse Microsoft Access database files (.mdb, .accdb)."""

    def parse(
        self,
        file_path: str,
        selected_tables: Optional[List[str]] = None,
    ) -> SourceSchema:
        """
        Parse Access database file and return schema.

        Args:
            file_path: Path to .mdb or .accdb file
            selected_tables: Optional list of table names to include.
                           If None, include all tables.

        Returns:
            SourceSchema: Parsed schema with tables

        Raises:
            RuntimeError: If pandas not installed or file cannot be read
        """
        if not HAS_PANDAS:
            raise RuntimeError(
                "pandas is required for Access file parsing. "
                "Install with: pip install pandas"
            )

        try:
            # Read all tables from Access file
            tables_dict = pd.read_excel(file_path, sheet_name=None)
        except Exception:
            # Try with openpyxl as fallback (for ACCDB files)
            try:
                import openpyxl
                from openpyxl import load_workbook
                wb = load_workbook(file_path)
                tables_dict = {sheet.title: pd.read_excel(file_path, sheet_name=sheet.title)
                              for sheet in wb.worksheets}
            except Exception as e:
                raise RuntimeError(
                    f"Failed to parse Access file. "
                    f"Ensure pandas and openpyxl are installed. Error: {str(e)}"
                )

        schema = SourceSchema(database_type="access", created_at=None)

        # Process each table
        for table_name, df in tables_dict.items():
            # Filter by selected_tables if provided
            if selected_tables and table_name not in selected_tables:
                continue

            if df.empty:
                continue

            # Extract columns from dataframe
            columns = []
            for col_name in df.columns:
                # Infer type from pandas dtype
                dtype = df[col_name].dtype
                inferred_type = self._map_pandas_dtype(dtype)

                col = SourceColumn(
                    name=str(col_name).strip(),
                    type_name=inferred_type,
                    nullable=df[col_name].isnull().any(),
                    default_value=None,
                )
                columns.append(col)

            # Create table
            table = SourceTable(
                name=table_name,
                columns=columns,
                estimated_rows=len(df),
                primary_key=None,
                constraints=[],
                foreign_keys=[],
            )

            schema.tables.append(table)

        return schema

    def _map_pandas_dtype(self, dtype) -> str:
        """
        Map pandas dtype to SQL type name.

        Args:
            dtype: pandas dtype object

        Returns:
            str: SQL type name
        """
        dtype_str = str(dtype).lower()

        # Numeric types
        if 'int' in dtype_str:
            return "INTEGER"
        elif 'float' in dtype_str:
            return "FLOAT"

        # Date/time types
        elif 'datetime' in dtype_str or 'timestamp' in dtype_str:
            return "DATETIME"
        elif 'date' in dtype_str:
            return "DATE"

        # Boolean
        elif 'bool' in dtype_str:
            return "BOOLEAN"

        # String/object
        else:
            return "VARCHAR"
