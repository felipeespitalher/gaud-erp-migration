"""Parser para SQL dumps."""
import re
from typing import List, Optional
import sqlparse
from sqlparse.sql import Identifier, IdentifierList, Parenthesis, Token
from src.schema.models import SourceSchema, SourceTable, SourceColumn, ForeignKey, Constraint
from src.parser.backup_parser import DatabaseBackupParser
from src.parser.dialect_detector import SqlDialectDetector


class SqlParser(DatabaseBackupParser):
    """Parser de SQL dump."""

    TYPE_MAPPING = {
        # PostgreSQL
        "serial": "INT",
        "bigserial": "BIGINT",
        "uuid": "UUID",
        "boolean": "BOOLEAN",
        "integer": "INT",
        "bigint": "BIGINT",
        "smallint": "SMALLINT",
        "decimal": "DECIMAL",
        "numeric": "DECIMAL",
        "real": "FLOAT",
        "double precision": "DOUBLE",
        "varchar": "VARCHAR",
        "character varying": "VARCHAR",
        "text": "TEXT",
        "date": "DATE",
        "time": "TIME",
        "timestamp": "TIMESTAMP",
        "timestamp without time zone": "TIMESTAMP",
        "timestamp with time zone": "TIMESTAMPTZ",
        "json": "JSON",
        "jsonb": "JSONB",
        # MySQL
        "int": "INT",
        "tinyint": "TINYINT",
        "mediumint": "MEDIUMINT",
        "float": "FLOAT",
        "double": "DOUBLE",
        "char": "CHAR",
        "longtext": "TEXT",
        "mediumtext": "TEXT",
        "longblob": "BLOB",
        "enum": "VARCHAR",
        "set": "VARCHAR",
    }

    @staticmethod
    def normalize_type(sql_type: str) -> str:
        """Normaliza tipo SQL para padrão comum."""
        sql_type = sql_type.lower().strip()

        # Remove (size) ou (precision, scale)
        sql_type = re.sub(r'\([^)]*\)', '', sql_type).strip()

        for key, value in SqlParser.TYPE_MAPPING.items():
            if sql_type.startswith(key):
                return value

        return sql_type.upper()

    def __init__(self, dialect: Optional[str] = None):
        """Initialize parser with optional dialect."""
        self.dialect = dialect

    def parse(
        self,
        sql_content: str,
        selected_tables: Optional[List[str]] = None,
    ) -> SourceSchema:
        """
        Parse SQL dump completo.

        Args:
            sql_content: SQL dump content
            selected_tables: Optional list of table names to include

        Returns:
            SourceSchema: Parsed schema, optionally filtered by selected_tables
        """
        # Auto-detect dialect if not provided
        if not self.dialect:
            self.dialect = SqlDialectDetector.detect(sql_content)

        schema = SourceSchema(database_type=self.dialect)

        # Parse com sqlparse
        parsed = sqlparse.parse(sql_content)

        for statement in parsed:
            # CREATE TABLE statements
            if statement.get_type() == "CREATE":
                table = SqlParser._parse_create_table(statement.value)
                if table:
                    # Filter by selected tables if provided
                    if selected_tables is None or table.name in selected_tables:
                        schema.tables.append(table)

        # Calcular totais
        schema.total_estimated_rows = sum(t.estimated_rows for t in schema.tables)

        return schema

    @staticmethod
    def _parse_create_table(statement: str) -> Optional[SourceTable]:
        """Parse um statement CREATE TABLE."""
        # Regex para encontrar CREATE TABLE
        match = re.match(
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["\`]?(\w+)["\`]?\s*\((.*)\)',
            statement,
            re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return None

        table_name = match.group(1)
        columns_def = match.group(2)

        table = SourceTable(name=table_name)

        # Parse colunas
        column_lines = SqlParser._split_column_definitions(columns_def)

        for line in column_lines:
            col = SqlParser._parse_column_definition(line)
            if col:
                table.columns.append(col)

            # Parse constraints
            constraint = SqlParser._parse_constraint_definition(line)
            if constraint:
                table.constraints.append(constraint)
                if constraint.type == "PRIMARY_KEY":
                    table.primary_keys = constraint.columns

        return table

    @staticmethod
    def _split_column_definitions(columns_def: str) -> List[str]:
        """Divide definições de colunas/constraints."""
        # Simples split por comma, mas evita commas dentro de parênteses
        lines = []
        current = ""
        depth = 0

        for char in columns_def:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "," and depth == 0:
                lines.append(current.strip())
                current = ""
                continue

            current += char

        if current.strip():
            lines.append(current.strip())

        return lines

    @staticmethod
    def _parse_column_definition(line: str) -> Optional[SourceColumn]:
        """Parse uma linha de definição de coluna."""
        # Pula constraint lines
        if any(keyword in line.upper() for keyword in ["PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK", "CONSTRAINT"]):
            return None

        # Regex para coluna
        match = re.match(
            r'["\`]?(\w+)["\`]?\s+(\w+(?:\([^)]*\))?)\s*(.*)',
            line,
            re.IGNORECASE,
        )

        if not match:
            return None

        col_name = match.group(1)
        col_type = match.group(2)
        col_flags = match.group(3).upper()

        column = SourceColumn(
            name=col_name,
            type=SqlParser.normalize_type(col_type),
            nullable="NOT NULL" not in col_flags,
            primary_key="PRIMARY KEY" in col_flags,
            unique="UNIQUE" in col_flags,
            auto_increment="AUTO_INCREMENT" in col_flags or "SERIAL" in col_type.upper(),
        )

        # Extract default value
        default_match = re.search(r'DEFAULT\s+([^\s,]+)', col_flags)
        if default_match:
            column.default = default_match.group(1)

        return column

    @staticmethod
    def _parse_constraint_definition(line: str) -> Optional[Constraint]:
        """Parse uma constraint line."""
        line = line.strip()

        # PRIMARY KEY
        if line.upper().startswith("PRIMARY KEY"):
            match = re.search(r'\(([^)]+)\)', line)
            if match:
                cols = [c.strip().strip('`"') for c in match.group(1).split(",")]
                return Constraint(name="pk", type="PRIMARY_KEY", columns=cols)

        # UNIQUE
        if line.upper().startswith("UNIQUE"):
            match = re.search(r'\(([^)]+)\)', line)
            if match:
                cols = [c.strip().strip('`"') for c in match.group(1).split(",")]
                return Constraint(name="unique", type="UNIQUE", columns=cols)

        # FOREIGN KEY
        if line.upper().startswith("FOREIGN KEY"):
            # Regex: FOREIGN KEY (col) REFERENCES table(col)
            match = re.search(
                r'FOREIGN\s+KEY\s+\(([^)]+)\)\s+REFERENCES\s+["\`]?(\w+)["\`]?\s*\(([^)]+)\)',
                line,
                re.IGNORECASE,
            )
            if match:
                local_col = match.group(1).strip().strip('`"')
                ref_table = match.group(2)
                ref_col = match.group(3).strip().strip('`"')
                return Constraint(
                    name="fk",
                    type="FOREIGN_KEY",
                    columns=[local_col, ref_table, ref_col],
                )

        return None

    @staticmethod
    def estimate_rows(sql_content: str) -> int:
        """Estima número de linhas nos INSERT statements."""
        insert_count = len(re.findall(r'INSERT\s+INTO', sql_content, re.IGNORECASE))
        return insert_count
