"""Data mapping model."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class MappingRule:
    """Represents a mapping from source to target."""

    source_table: str
    source_columns: List[str]
    target_table: Optional[str]
    target_field: Optional[str]
    mapping_type: str = "1-to-1"  # "1-to-1", "N-to-1", "1-to-N"
    transformer: str = "NONE"
    transformer_config: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    ignored: bool = False
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_table": self.source_table,
            "source_columns": self.source_columns,
            "target_table": self.target_table,
            "target_field": self.target_field,
            "mapping_type": self.mapping_type,
            "transformer": self.transformer,
            "transformer_config": self.transformer_config,
            "confidence": self.confidence,
            "ignored": self.ignored,
            "description": self.description,
        }
