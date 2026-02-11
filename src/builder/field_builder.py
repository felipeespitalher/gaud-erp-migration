"""
Field Builder - Constructs individual API fields and nested structures

Supports:
- Direct field mapping (source column → target field)
- Nested object/array construction
- AttributeMapping (maps columns to attributes[] in Gaud format)
- Type transformations
- Custom transformers
"""

from dataclasses import dataclass, field as dataclass_field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


@dataclass
class AttributeMapping:
    """Maps a source column to an attribute in Gaud's attributes[] array"""

    source_column: str  # BANCO column name (e.g., "peso", "altura")
    attribute_id: Optional[int] = None  # Gaud attribute ID (e.g., 1 for "Peso")
    attribute_name: str = ""  # Gaud attribute name (e.g., "Peso", "Altura")
    transformer: Optional[str] = None  # Transformer to apply (e.g., "FORMAT_FLOAT")
    skip_if_null: bool = True  # Skip if column value is null
    format_string: Optional[str] = None  # Format string for output (e.g., "{value} kg")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source_column": self.source_column,
            "attribute_id": self.attribute_id,
            "attribute_name": self.attribute_name,
            "transformer": self.transformer,
            "skip_if_null": self.skip_if_null,
            "format_string": self.format_string,
        }


@dataclass
class FieldMapping:
    """Maps a source field/column to a target field in Gaud API"""

    source: str  # Source column name
    target: str  # Target field name in API
    type: str = "direct"  # "direct", "nested", "array", "attribute"
    transformer: Optional[str] = None  # Transformer to apply
    nested_endpoint: Optional[str] = None  # For nested objects, the sub-endpoint
    attribute_mappings: List[AttributeMapping] = dataclass_field(default_factory=list)  # For attributes[]
    foreign_key_resolver: Optional[Callable] = None  # Function to resolve FK
    default_value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "transformer": self.transformer,
            "nested_endpoint": self.nested_endpoint,
            "attribute_mappings": [am.to_dict() for am in self.attribute_mappings],
            "default_value": self.default_value,
        }


class FieldBuilder:
    """Builds individual fields for Gaud API payloads"""

    def __init__(self, transformers: Optional[Dict[str, Callable]] = None):
        """
        Initialize FieldBuilder

        Args:
            transformers: Dictionary of transformer functions {name: callable}
        """
        self.transformers = transformers or {}

    def build_field(
        self,
        mapping: FieldMapping,
        source_data: Dict[str, Any],
        id_mappings: Optional[Dict[str, Dict[int, int]]] = None,
    ) -> tuple[str, Any]:
        """
        Build a single field for Gaud API payload

        Args:
            mapping: Field mapping configuration
            source_data: Source row data
            id_mappings: ID mappings for FK resolution (e.g., {"marcas": {2: 100}})

        Returns:
            Tuple of (target_field_name, field_value)
        """
        # Handle different field types first (some don't need source column)
        if mapping.type == "attribute":
            # Build attributes[] array from attribute mappings
            # No need to get source_value for this type
            attributes = self._build_attributes(
                mapping.attribute_mappings,
                source_data
            )
            return mapping.target, attributes if attributes else None

        # For other types, get source value
        source_value = source_data.get(mapping.source, mapping.default_value)

        # Handle None/null values
        if source_value is None:
            if mapping.default_value is not None:
                source_value = mapping.default_value
            else:
                return mapping.target, None

        # Apply transformation if specified
        if mapping.transformer:
            source_value = self._apply_transformer(source_value, mapping.transformer)

        # Handle different field types
        if mapping.type == "direct":
            return mapping.target, source_value

        elif mapping.type == "nested":
            # Build nested object (e.g., {"id": value})
            return mapping.target, {"id": source_value}

        elif mapping.type == "array":
            # Build array of nested objects (e.g., [{id: value}])
            return mapping.target, [{"id": source_value}]

        else:
            logger.warning(f"Unknown field type: {mapping.type}")
            return mapping.target, source_value

    def _build_attributes(
        self,
        attribute_mappings: List[AttributeMapping],
        source_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Build Gaud attributes[] array from attribute mappings

        Transforms:
            BANCO row: {peso: 2.5, altura: 10, largura: 15}
        Into:
            [
                {"attribute": {"id": 1}, "value": "2.5"},
                {"attribute": {"id": 2}, "value": "10"},
                {"attribute": {"id": 3}, "value": "15"}
            ]
        """
        attributes = []

        for attr_mapping in attribute_mappings:
            # Get source value
            source_value = source_data.get(attr_mapping.source_column)

            # Skip if null and skip_if_null is True
            if source_value is None:
                if attr_mapping.skip_if_null:
                    continue
                source_value = ""

            # Apply transformer if specified
            if attr_mapping.transformer:
                source_value = self._apply_transformer(source_value, attr_mapping.transformer)

            # Format the value if format_string is specified
            if attr_mapping.format_string:
                source_value = attr_mapping.format_string.format(value=source_value)
            else:
                # Convert to string by default
                source_value = str(source_value)

            # Build attribute entry
            attribute = {
                "attribute": {
                    "id": attr_mapping.attribute_id,
                    "name": attr_mapping.attribute_name,
                },
                "value": source_value,
            }
            attributes.append(attribute)

        return attributes

    def _apply_transformer(self, value: Any, transformer_name: str) -> Any:
        """Apply a transformer function to a value"""
        if transformer_name not in self.transformers:
            logger.warning(f"Unknown transformer: {transformer_name}")
            return value

        transformer = self.transformers[transformer_name]
        try:
            return transformer(value)
        except Exception as e:
            logger.error(f"Error applying transformer {transformer_name}: {e}")
            return value

    @staticmethod
    def build_nested_object(
        nested_fields: Dict[str, FieldMapping],
        source_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build a nested object with multiple fields

        Example:
            nested_fields = {
                "id": FieldMapping("brand_id", "id"),
                "name": FieldMapping("brand_name", "name"),
            }
        """
        result = {}
        builder = FieldBuilder()

        for field_name, mapping in nested_fields.items():
            target, value = builder.build_field(mapping, source_data, **kwargs)
            if value is not None:
                result[target] = value

        return result

    @staticmethod
    def build_array_of_objects(
        item_mappings: List[FieldMapping],
        source_data: Dict[str, Any],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Build an array of objects (e.g., multiple productBrands)

        For now, supports a single item per source row.
        Full N-to-many relationships would need more complex logic.
        """
        builder = FieldBuilder()
        result = {}

        for mapping in item_mappings:
            target, value = builder.build_field(mapping, source_data, **kwargs)
            if value is not None:
                result[target] = value

        return [result] if result else []
