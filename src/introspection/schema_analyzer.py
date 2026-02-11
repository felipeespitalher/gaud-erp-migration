"""
Schema Analyzer - Parses OpenAPI/Swagger definitions and extracts field structures.

Supports:
- OpenAPI 3.0 schema parsing
- Nested object/array structure detection
- $ref resolution
- Type inference
- Field validation rules extraction
"""

from dataclasses import dataclass, field as dataclass_field
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FieldType(str, Enum):
    """Supported field types in API schema"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    DATE = "string"  # date format
    DATETIME = "string"  # date-time format
    UUID = "string"  # uuid format
    UNKNOWN = "unknown"


@dataclass
class EndpointField:
    """Represents a single field in an API endpoint"""
    name: str
    type: FieldType
    required: bool = False
    description: str = ""
    format: Optional[str] = None  # "date", "date-time", "uuid", etc.
    nested_fields: Dict[str, "EndpointField"] = dataclass_field(default_factory=dict)
    array_item_type: Optional["EndpointField"] = None
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    enum_values: List[Any] = dataclass_field(default_factory=list)

    def is_nested_object(self) -> bool:
        """Check if field is a nested object"""
        return self.type == FieldType.OBJECT and len(self.nested_fields) > 0

    def is_array(self) -> bool:
        """Check if field is an array"""
        return self.type == FieldType.ARRAY

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "type": self.type.value,
            "required": self.required,
            "description": self.description,
            "format": self.format,
            "is_nested": self.is_nested_object(),
            "is_array": self.is_array(),
            "nested_fields": {k: v.to_dict() for k, v in self.nested_fields.items()},
            "array_item_type": self.array_item_type.to_dict() if self.array_item_type else None,
            "enum_values": self.enum_values,
        }


@dataclass
class EndpointSchema:
    """Schema for a single API endpoint"""
    path: str
    method: str  # "GET", "POST", "PUT", "PATCH", "DELETE"
    description: str = ""
    request_body_fields: Dict[str, EndpointField] = dataclass_field(default_factory=dict)
    response_fields: Dict[str, EndpointField] = dataclass_field(default_factory=dict)
    required_fields: List[str] = dataclass_field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "path": self.path,
            "method": self.method,
            "description": self.description,
            "request_body_fields": {k: v.to_dict() for k, v in self.request_body_fields.items()},
            "response_fields": {k: v.to_dict() for k, v in self.response_fields.items()},
            "required_fields": self.required_fields,
        }


@dataclass
class APISchema:
    """Complete API schema extracted from OpenAPI/Swagger"""
    title: str = ""
    version: str = ""
    base_url: str = ""
    endpoints: Dict[str, EndpointSchema] = dataclass_field(default_factory=dict)
    definitions: Dict[str, Dict[str, Any]] = dataclass_field(default_factory=dict)  # $defs cache

    def get_endpoint(self, path: str, method: str = "POST") -> Optional[EndpointSchema]:
        """Get endpoint schema by path and method"""
        key = f"{method} {path}"
        return self.endpoints.get(key)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "title": self.title,
            "version": self.version,
            "base_url": self.base_url,
            "endpoints": {k: v.to_dict() for k, v in self.endpoints.items()},
        }


class SchemaAnalyzer:
    """Analyzes OpenAPI/Swagger schemas and extracts field structures"""

    def __init__(self):
        self.api_schema = APISchema()
        self._ref_cache: Dict[str, Dict[str, Any]] = {}
        self._processing_refs: Set[str] = set()  # Prevent circular refs

    def analyze_openapi_spec(self, spec: Dict[str, Any]) -> APISchema:
        """
        Analyze OpenAPI 3.0 specification

        Args:
            spec: OpenAPI spec dictionary (parsed from JSON/YAML)

        Returns:
            APISchema with extracted endpoint structures
        """
        # Extract metadata
        self.api_schema.title = spec.get("info", {}).get("title", "Unknown API")
        self.api_schema.version = spec.get("info", {}).get("version", "1.0.0")

        # Extract base URL
        servers = spec.get("servers", [])
        if servers:
            self.api_schema.base_url = servers[0].get("url", "")

        # Cache all definitions for $ref resolution
        if "components" in spec and "schemas" in spec["components"]:
            self.api_schema.definitions = spec["components"]["schemas"]

        # Process all paths
        paths = spec.get("paths", {})
        for path, path_item in paths.items():
            self._process_path(path, path_item)

        logger.info(f"Analyzed {len(self.api_schema.endpoints)} endpoints")
        return self.api_schema

    def _process_path(self, path: str, path_item: Dict[str, Any]) -> None:
        """Process a single path and its methods"""
        for method, operation in path_item.items():
            if method.lower() not in ["get", "post", "put", "patch", "delete"]:
                continue

            endpoint_schema = EndpointSchema(
                path=path,
                method=method.upper(),
                description=operation.get("summary", "")
            )

            # Process request body
            if "requestBody" in operation:
                content = operation["requestBody"].get("content", {})
                schema_obj = content.get("application/json", {}).get("schema")
                if schema_obj:
                    endpoint_schema.request_body_fields = self._extract_fields(schema_obj)
                    required = operation["requestBody"].get("required", False)
                    if required:
                        endpoint_schema.required_fields = list(endpoint_schema.request_body_fields.keys())

            # Process responses
            if "responses" in operation:
                responses = operation["responses"]
                # Use 200/201 response as the main one
                for status_code in ["200", "201", "default"]:
                    if status_code in responses:
                        response_obj = responses[status_code]
                        content = response_obj.get("content", {})
                        schema_obj = content.get("application/json", {}).get("schema")
                        if schema_obj:
                            endpoint_schema.response_fields = self._extract_fields(schema_obj)
                        break

            key = f"{endpoint_schema.method} {endpoint_schema.path}"
            self.api_schema.endpoints[key] = endpoint_schema

    def _extract_fields(self, schema_obj: Dict[str, Any], name: str = "") -> Dict[str, EndpointField]:
        """
        Extract field definitions from a schema object

        Supports:
        - Direct properties
        - $ref references
        - Nested objects
        - Arrays
        """
        fields = {}

        # Handle $ref
        if "$ref" in schema_obj:
            ref_schema = self._resolve_ref(schema_obj["$ref"])
            if ref_schema:
                schema_obj = ref_schema

        # Handle allOf
        if "allOf" in schema_obj:
            for sub_schema in schema_obj["allOf"]:
                fields.update(self._extract_fields(sub_schema, name))
            return fields

        # Extract properties
        properties = schema_obj.get("properties", {})
        required_list = schema_obj.get("required", [])

        for prop_name, prop_schema in properties.items():
            field = self._create_field(prop_name, prop_schema, prop_name in required_list)
            fields[prop_name] = field

        return fields

    def _create_field(
        self,
        name: str,
        schema_obj: Dict[str, Any],
        required: bool = False,
    ) -> EndpointField:
        """
        Create an EndpointField from schema object

        Handles:
        - Basic types (string, integer, boolean, etc.)
        - Objects with nested fields
        - Arrays with item types
        - $ref references
        - Type formats (date, date-time, uuid, etc.)
        """
        # Handle $ref
        if "$ref" in schema_obj:
            ref_schema = self._resolve_ref(schema_obj["$ref"])
            if ref_schema:
                schema_obj = ref_schema

        # Determine field type
        schema_type = schema_obj.get("type", "object")
        field_format = schema_obj.get("format")
        description = schema_obj.get("description", "")

        # Map field type
        field_type = FieldType(schema_type) if schema_type in [ft.value for ft in FieldType] else FieldType.UNKNOWN

        # Create field instance
        field = EndpointField(
            name=name,
            type=field_type,
            required=required,
            description=description,
            format=field_format,
            pattern=schema_obj.get("pattern"),
            min_length=schema_obj.get("minLength"),
            max_length=schema_obj.get("maxLength"),
            enum_values=schema_obj.get("enum", []),
        )

        # Handle nested objects
        if field_type == FieldType.OBJECT:
            nested = self._extract_fields(schema_obj)
            field.nested_fields = nested

        # Handle arrays
        elif field_type == FieldType.ARRAY:
            items_schema = schema_obj.get("items", {})
            if items_schema:
                # Create a temporary field for array items
                item_type = items_schema.get("type", "object")
                item_field = self._create_field(
                    f"{name}_item",
                    items_schema,
                    required=False
                )
                field.array_item_type = item_field

        return field

    def _resolve_ref(self, ref: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a $ref reference (e.g., "#/components/schemas/Product")

        Supports:
        - OpenAPI 3.0 style: #/components/schemas/Name
        - Circular reference prevention
        """
        # Check cache first
        if ref in self._ref_cache:
            return self._ref_cache[ref]

        # Prevent circular references
        if ref in self._processing_refs:
            logger.warning(f"Circular reference detected: {ref}")
            return None

        try:
            # Extract reference path (e.g., "components/schemas/Product")
            if ref.startswith("#/"):
                ref_path = ref[2:].split("/")
                obj = self.api_schema.definitions

                # Navigate the reference path
                for key in ref_path[2:]:  # Skip first 2 parts (components/schemas)
                    if isinstance(obj, dict) and key in obj:
                        obj = obj[key]
                    else:
                        return None

                if isinstance(obj, dict):
                    self._ref_cache[ref] = obj
                    return obj

        except Exception as e:
            logger.error(f"Error resolving reference {ref}: {e}")

        return None
