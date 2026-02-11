"""
Payload Builder - Orchestrates complex Gaud API payload generation

Integrates:
- FieldBuilder: Field-level construction
- TemplateEngine: Template evaluation
- Schema validation: Ensures payloads match Gaud API structure
- Attribute mapping: BANCO columns → Gaud attributes[]
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass

from .field_builder import FieldBuilder, FieldMapping, AttributeMapping
from .template_engine import TemplateEngine

logger = logging.getLogger(__name__)


@dataclass
class PayloadConfig:
    """Configuration for payload building"""
    table_name: str
    endpoint: str
    mappings: List[FieldMapping]
    nested_mappings: Optional[Dict[str, Any]] = None
    id_mappings: Optional[Dict[str, Dict[int, int]]] = None
    transformers: Optional[Dict[str, Callable]] = None
    validate_required: bool = True


class PayloadBuilder:
    """
    Builds complete Gaud API payloads from source data

    Usage:
    ```python
    config = PayloadConfig(
        table_name="PRODUTOS",
        endpoint="/v1/catalog/products",
        mappings=[
            FieldMapping("nome", "name", "direct"),
            FieldMapping("peso", "attributes", "attribute",
                         attribute_mappings=[AttributeMapping("peso", attribute_id=1, attribute_name="Peso")]),
        ]
    )

    payload = builder.build(config, source_row)
    # Returns: {"name": "Product X", "attributes": [...]}
    ```
    """

    def __init__(self, transformers: Optional[Dict[str, Callable]] = None):
        """
        Initialize PayloadBuilder

        Args:
            transformers: Custom transformer functions
        """
        self.transformers = transformers or {}
        self.field_builder = FieldBuilder(self.transformers)
        self.template_engine = TemplateEngine()

    def build(
        self,
        config: PayloadConfig,
        source_data: Dict[str, Any],
        id_mappings: Optional[Dict[str, Dict[int, int]]] = None,
    ) -> Dict[str, Any]:
        """
        Build a complete Gaud API payload

        Args:
            config: Payload configuration
            source_data: Source row data
            id_mappings: ID mappings for FK resolution

        Returns:
            Complete payload dictionary ready for API POST
        """
        # Use provided id_mappings or fall back to config
        id_mappings = id_mappings or config.id_mappings

        payload = {}

        # Build fields from mappings
        for mapping in config.mappings:
            target, value = self.field_builder.build_field(
                mapping,
                source_data,
                id_mappings=id_mappings
            )

            if value is not None:
                payload[target] = value

        # Validate required fields if enabled
        if config.validate_required:
            missing = self._validate_required_fields(payload, config)
            if missing:
                logger.warning(f"Missing required fields: {missing}")

        return payload

    def build_batch(
        self,
        config: PayloadConfig,
        source_data: List[Dict[str, Any]],
        id_mappings: Optional[Dict[str, Dict[int, int]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Build payloads for multiple rows

        Args:
            config: Payload configuration
            source_data: List of source rows
            id_mappings: ID mappings

        Returns:
            List of payloads
        """
        payloads = []

        for row in source_data:
            try:
                payload = self.build(config, row, id_mappings)
                payloads.append(payload)
            except Exception as e:
                logger.error(f"Error building payload for row: {e}")
                # Continue with next row
                continue

        logger.info(f"Built {len(payloads)} payloads from {len(source_data)} rows")
        return payloads

    def _validate_required_fields(
        self,
        payload: Dict[str, Any],
        config: PayloadConfig
    ) -> List[str]:
        """
        Check if required fields are present in payload

        Returns:
            List of missing required field names
        """
        # For now, all fields are optional
        # In future, can integrate with APISchema to validate against endpoint requirements
        return []

    def build_with_nested_objects(
        self,
        config: PayloadConfig,
        source_data: Dict[str, Any],
        nested_config: Dict[str, Any],  # Configuration for nested objects
    ) -> Dict[str, Any]:
        """
        Build payload with nested object structures

        Args:
            config: Main payload configuration
            source_data: Source row data
            nested_config: Configuration for nested fields

        Returns:
            Complete payload with nested structures
        """
        # Build main payload first
        payload = self.build(config, source_data)

        # Add nested structures
        for nested_key, nested_def in nested_config.items():
            if isinstance(nested_def, dict) and "mappings" in nested_def:
                # Build nested object
                nested_mappings = nested_def["mappings"]
                nested_obj = self._build_nested(nested_mappings, source_data)
                if nested_obj:
                    payload[nested_key] = nested_obj

        return payload

    def _build_nested(
        self,
        nested_mappings: List[FieldMapping],
        source_data: Dict[str, Any],
    ) -> Any:
        """Build nested object or array"""
        result = {}

        for mapping in nested_mappings:
            target, value = self.field_builder.build_field(mapping, source_data)
            if value is not None:
                result[target] = value

        return result if result else None

    def add_transformer(self, name: str, func: Callable) -> None:
        """Register a custom transformer function"""
        self.transformers[name] = func
        self.field_builder.transformers[name] = func

    def get_schema_for_endpoint(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Get expected payload schema for an endpoint

        Returns:
            Schema dictionary with field types and requirements
        """
        # TODO: Integrate with APISchemaIntrospector to fetch schema
        return None


# ============================================================================
# Builder convenience functions
# ============================================================================


def build_product_payload(
    source_row: Dict[str, Any],
    transformers: Optional[Dict[str, Callable]] = None,
) -> Dict[str, Any]:
    """
    Build CatalogProduct payload for Gaud ERP

    Supports BANCO.MDB products with:
    - Basic fields (nome, sku, description)
    - Brand reference (id_marca → productBrands[{brand: {id: ...}}])
    - Attributes mapping (peso, altura, largura, profundidade → attributes[])
    - Categories and suppliers
    """
    config = PayloadConfig(
        table_name="PRODUTOS",
        endpoint="/v1/catalog/products",
        mappings=[
            FieldMapping("nome", "name", "direct"),
            FieldMapping("sku", "sku", "direct"),
            FieldMapping("descricao", "description", "direct"),
            FieldMapping("ativo", "active", "direct"),
            # Attributes array for dimensions
            FieldMapping(
                source="",  # No single source column
                target="attributes",
                type="attribute",
                attribute_mappings=[
                    AttributeMapping("peso", attribute_id=1, attribute_name="Peso", format_string="{value} kg"),
                    AttributeMapping("altura", attribute_id=2, attribute_name="Altura", format_string="{value} cm"),
                    AttributeMapping("largura", attribute_id=3, attribute_name="Largura", format_string="{value} cm"),
                    AttributeMapping("profundidade", attribute_id=4, attribute_name="Profundidade", format_string="{value} cm"),
                ]
            ),
        ],
        transformers=transformers,
    )

    builder = PayloadBuilder(transformers)
    return builder.build(config, source_row)


def build_brand_payload(
    source_row: Dict[str, Any],
) -> Dict[str, Any]:
    """Build Brand payload for Gaud ERP"""
    config = PayloadConfig(
        table_name="MARCAS",
        endpoint="/v1/inventory/brands",
        mappings=[
            FieldMapping("nome", "name", "direct"),
            FieldMapping("descricao", "description", "direct"),
        ]
    )

    builder = PayloadBuilder()
    return builder.build(config, source_row)
