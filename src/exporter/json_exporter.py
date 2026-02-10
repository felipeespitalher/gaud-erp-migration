"""JSON exporter."""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from src.schema.models import SourceSchema
from src.mapper.mapping import MappingRule


class JsonExporter:
    """Export migration data to JSON."""

    def export(
        self,
        output_file: Path,
        source_schema: SourceSchema,
        mappings: List[MappingRule],
    ) -> None:
        """Export to JSON file."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "source_database": source_schema.database_type,
                "source_tables": len(source_schema.tables),
                "total_records": source_schema.total_estimated_rows,
                "validation_result": "PENDING",
            },
            "schema": source_schema.to_dict(),
            "mappings": [m.to_dict() for m in mappings],
            "data": {},  # Placeholder for actual data
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
