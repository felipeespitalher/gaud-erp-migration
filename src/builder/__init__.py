"""
Payload Builder Module - Phase 2 Implementation

Builds complex nested Gaud API payloads from source data with:
- Field mapping and transformations
- Nested object/array construction
- AttributeMapping support (BANCO columns → Gaud attributes[])
- Template-based payload generation
"""

from .payload_builder import PayloadBuilder
from .field_builder import FieldBuilder, AttributeMapping
from .template_engine import TemplateEngine

__all__ = [
    "PayloadBuilder",
    "FieldBuilder",
    "AttributeMapping",
    "TemplateEngine",
]
