"""CSV file parser with auto-delimiter detection."""
import csv
from io import StringIO
from typing import Optional, List
import re

from src.parser.backup_parser import DatabaseBackupParser
from src.schema.models import SourceSchema, SourceTable, SourceColumn


class CsvParser(DatabaseBackupParser):
    """Parse CSV files and extract schema."""

    # Common delimiters
    DELIMITERS = [',', ';', '|', '\t']

    def parse(
        self,
        content: str,
        selected_tables: Optional[List[str]] = None,
    ) -> SourceSchema:
        """
        Parse CSV content and return schema.

        Args:
            content: CSV file content (as string)
            selected_tables: Optional list of table names to include.
                           For CSV, this is typically just the filename/table name.

        Returns:
            SourceSchema: Parsed schema with one table

        Raises:
            ParseException: If parsing fails
        """
        # Auto-detect delimiter
        delimiter = self._detect_delimiter(content)

        # Parse CSV
        rows = self._read_csv(content, delimiter)

        if not rows:
            schema = SourceSchema(database_type="csv", created_at=None)
            return schema

        # Extract headers (first row)
        headers = rows[0]

        # Infer types from data (sample first 100 rows)
        sample_rows = rows[1:101]
        inferred_types = self._infer_types(headers, sample_rows)

        # Create table definition
        table_name = "data"  # Default table name for CSV
        columns = []

        for i, header in enumerate(headers):
            col = SourceColumn(
                name=header.strip(),
                type_name=inferred_types.get(i, "VARCHAR"),
                nullable=True,
                default_value=None,
            )
            columns.append(col)

        table = SourceTable(
            name=table_name,
            columns=columns,
            estimated_rows=len(rows) - 1,  # Exclude header
            primary_key=None,
            constraints=[],
            foreign_keys=[],
        )

        schema = SourceSchema(
            database_type="csv",
            created_at=None,
        )
        schema.tables.append(table)

        return schema

    def _detect_delimiter(self, content: str) -> str:
        """
        Auto-detect CSV delimiter.

        Returns:
            str: Most likely delimiter
        """
        # Sample first 1000 characters
        sample = content[:1000]

        # Count occurrences of each delimiter
        counts = {}
        for delimiter in self.DELIMITERS:
            counts[delimiter] = sample.count(delimiter)

        # Return delimiter with most occurrences
        best_delimiter = max(counts, key=counts.get)

        # Fallback to comma if no clear winner
        if counts[best_delimiter] == 0:
            return ','

        return best_delimiter

    def _read_csv(self, content: str, delimiter: str) -> List[List[str]]:
        """
        Read CSV content and return rows.

        Args:
            content: CSV content as string
            delimiter: Field delimiter

        Returns:
            List[List[str]]: List of rows
        """
        try:
            reader = csv.reader(StringIO(content), delimiter=delimiter)
            rows = list(reader)
            return rows
        except Exception:
            # Fallback to comma delimiter
            reader = csv.reader(StringIO(content), delimiter=',')
            return list(reader)

    def _infer_types(self, headers: List[str], rows: List[List[str]]) -> dict:
        """
        Infer column types from data.

        Args:
            headers: Column headers
            rows: Sample data rows

        Returns:
            dict: {column_index: inferred_type}
        """
        inferred = {}

        for col_idx in range(len(headers)):
            # Default to VARCHAR
            inferred_type = "VARCHAR"

            # Sample values from column
            sample_values = []
            for row in rows:
                if col_idx < len(row):
                    val = row[col_idx].strip()
                    if val:  # Skip empty values
                        sample_values.append(val)

            if not sample_values:
                inferred_type = "VARCHAR"
            else:
                # Try to infer type from samples
                inferred_type = self._infer_type_from_sample(sample_values)

            inferred[col_idx] = inferred_type

        return inferred

    def _infer_type_from_sample(self, values: List[str]) -> str:
        """
        Infer type from sample values.

        Args:
            values: List of string values

        Returns:
            str: Inferred type name
        """
        if not values:
            return "VARCHAR"

        # Count type matches
        is_int_count = 0
        is_float_count = 0
        is_date_count = 0
        is_bool_count = 0

        for val in values:
            val = val.strip()

            # Check if integer
            try:
                int(val)
                is_int_count += 1
                continue
            except ValueError:
                pass

            # Check if float
            try:
                float(val)
                is_float_count += 1
                continue
            except ValueError:
                pass

            # Check if date (simple patterns)
            if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', val) or \
               re.match(r'^\d{4}-\d{2}-\d{2}', val) or \
               re.match(r'^\d{2}-\d{2}-\d{4}$', val):
                is_date_count += 1
                continue

            # Check if boolean
            if val.lower() in ('true', 'false', 'yes', 'no', '1', '0'):
                is_bool_count += 1
                continue

        # Determine type by majority
        total = len(values)
        threshold = 0.8  # 80% of values must match type

        if is_int_count >= total * threshold:
            return "INTEGER"
        elif is_float_count >= total * threshold:
            return "FLOAT"
        elif is_date_count >= total * threshold:
            return "DATE"
        elif is_bool_count >= total * threshold:
            return "BOOLEAN"
        else:
            return "VARCHAR"
