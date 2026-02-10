"""Data validation."""
from typing import List, Dict, Any

from src.schema.models import SourceSchema
from src.mapper.mapping import MappingRule


class DataValidator:
    """Validates data against schema."""

    def validate(
        self,
        source_schema: SourceSchema,
        mappings: List[MappingRule],
    ) -> List[str]:
        """Validate data."""
        errors = []

        # Check for missing target tables
        for mapping in mappings:
            if mapping.target_table is None and not mapping.ignored:
                errors.append(
                    f"Missing target for {mapping.source_table}.{mapping.source_columns[0]}"
                )

        # Check for type compatibility
        for table in source_schema.tables:
            for col in table.columns:
                if col.type not in ["VARCHAR", "INT", "BOOLEAN", "DATE", "TIMESTAMP", "UUID", "TEXT", "DECIMAL"]:
                    errors.append(f"Unknown type: {table.name}.{col.name} = {col.type}")

        return errors
