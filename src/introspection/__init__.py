"""
API Introspection Module - Phase 1 Implementation

Discovers endpoint structures automatically from Gaud API Swagger/OpenAPI schema.
Supports:
- OpenAPI 3.0 specification parsing
- Nested field detection
- Array/object structure mapping
- $ref resolution
- Schema caching (1 hour TTL)
"""

from .api_schema_introspector import ApiSchemaIntrospector
from .schema_analyzer import SchemaAnalyzer, APISchema, EndpointField, FieldType

__all__ = [
    "ApiSchemaIntrospector",
    "SchemaAnalyzer",
    "APISchema",
    "EndpointField",
    "FieldType",
]
