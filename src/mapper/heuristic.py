"""Heuristic mapping engine for auto-detecting schema mappings."""
from typing import List, Optional, Dict, Any
from difflib import SequenceMatcher

from src.mapper.mapping import MappingRule
from src.schema.models import SourceSchema, SourceTable, SourceColumn


class HeuristicMapper:
    """Auto-map source schema to target schema using heuristics."""

    COMMON_NAME_MAPPINGS = {
        "customer": "Customer",
        "customers": "Customer",
        "client": "Customer",
        "clients": "Customer",
        "user": "User",
        "users": "User",
        "product": "Product",
        "products": "Product",
        "order": "Order",
        "orders": "Order",
        "invoice": "Invoice",
        "invoices": "Invoice",
        "payment": "Payment",
        "payments": "Payment",
    }

    COMMON_COLUMN_MAPPINGS = {
        "id": "id",
        "uuid": "id",
        "guid": "id",
        "name": "name",
        "full_name": "name",
        "email": "email",
        "phone": "phone",
        "telephone": "phone",
        "created_at": "createdAt",
        "created_date": "createdAt",
        "updated_at": "updatedAt",
        "modified_at": "updatedAt",
        "deleted_at": "deletedAt",
    }

    def __init__(self, target_schema: Optional[Dict[str, Any]] = None):
        """Initialize mapper with optional target schema."""
        self.target_schema = target_schema or {}
        self.target_tables = self._extract_target_tables()

    def _extract_target_tables(self) -> Dict[str, Any]:
        """Extract table info from target schema."""
        tables = {}
        for table in self.target_schema.get("tables", []):
            tables[table["name"].lower()] = table
        return tables

    def suggest_mappings(self, source_schema: SourceSchema) -> List[MappingRule]:
        """Generate mapping suggestions for source schema."""
        mappings = []

        for source_table in source_schema.tables:
            target_table = self._find_target_table(source_table.name)

            if target_table:
                # Table mapping found - map columns
                for source_col in source_table.columns:
                    target_col = self._find_target_column(
                        source_col.name, target_table
                    )

                    mapping = MappingRule(
                        source_table=source_table.name,
                        source_columns=[source_col.name],
                        target_table=target_table["name"],
                        target_field=target_col or source_col.name,
                        mapping_type="1-to-1",
                        transformer="NONE",
                        confidence=0.9 if target_col else 0.6,
                    )

                    mappings.append(mapping)
            else:
                # Table mapping not found - skip or suggest N->1
                for source_col in source_table.columns:
                    mapping = MappingRule(
                        source_table=source_table.name,
                        source_columns=[source_col.name],
                        target_table=None,  # To be filled
                        target_field=None,
                        mapping_type="1-to-1",
                        transformer="NONE",
                        confidence=0.0,
                    )
                    mappings.append(mapping)

        return mappings

    def _find_target_table(self, source_table_name: str) -> Optional[Dict[str, Any]]:
        """Find matching target table."""
        source_lower = source_table_name.lower()

        # Exact match
        if source_lower in self.target_tables:
            return self.target_tables[source_lower]

        # Common name mapping
        if source_lower in self.COMMON_NAME_MAPPINGS:
            target_name = self.COMMON_NAME_MAPPINGS[source_lower]
            return self.target_tables.get(target_name.lower())

        # Fuzzy match
        best_match = None
        best_ratio = 0.7

        for target_name, target_table in self.target_tables.items():
            ratio = SequenceMatcher(None, source_lower, target_name).ratio()

            if ratio > best_ratio:
                best_ratio = ratio
                best_match = target_table

        return best_match

    def _find_target_column(
        self, source_col_name: str, target_table: Dict[str, Any]
    ) -> Optional[str]:
        """Find matching target column."""
        source_lower = source_col_name.lower()

        # Exact match
        for col in target_table.get("columns", []):
            if col["name"].lower() == source_lower:
                return col["name"]

        # Common mapping
        if source_lower in self.COMMON_COLUMN_MAPPINGS:
            target_col = self.COMMON_COLUMN_MAPPINGS[source_lower]
            for col in target_table.get("columns", []):
                if col["name"].lower() == target_col.lower():
                    return col["name"]

        # Fuzzy match
        best_match = None
        best_ratio = 0.75

        for col in target_table.get("columns", []):
            ratio = SequenceMatcher(None, source_lower, col["name"].lower()).ratio()

            if ratio > best_ratio:
                best_ratio = ratio
                best_match = col["name"]

        return best_match
