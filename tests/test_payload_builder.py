"""
Unit tests for PayloadBuilder Module (Phase 2)

Tests:
- FieldBuilder: Direct/nested/array/attribute field building
- AttributeMapping: Column-to-attributes[] transformation
- PayloadBuilder: Complete payload construction
- TemplateEngine: Template evaluation
"""

import pytest
from typing import Dict, Any

from src.builder.payload_builder import (
    PayloadBuilder,
    PayloadConfig,
    build_product_payload,
    build_brand_payload,
)
from src.builder.field_builder import (
    FieldBuilder,
    FieldMapping,
    AttributeMapping,
)
from src.builder.template_engine import TemplateEngine


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_banco_product():
    """Sample BANCO.MDB product row"""
    return {
        "id": 4910,
        "nome": "PNEU 175/60 R15",
        "sku": "P175",
        "descricao": "Pneu de alta performance",
        "peso": 2.5,
        "altura": 10,
        "largura": 15,
        "profundidade": 20,
        "preco": 150.00,
        "custo": 75.00,
        "id_marca": 2,
        "id_categoria": 1,
        "id_fornecedor": 5,
        "ativo": 1,
    }


@pytest.fixture
def sample_banco_brand():
    """Sample BANCO.MDB brand row"""
    return {
        "id": 2,
        "nome": "Michelin",
        "descricao": "Tire manufacturer",
    }


@pytest.fixture
def id_mappings():
    """Sample ID mappings (BANCO IDs → Gaud IDs)"""
    return {
        "marcas": {2: 100, 3: 101},
        "categorias": {1: 50, 5: 51},
        "fornecedores": {5: 20, 6: 21},
    }


@pytest.fixture
def transformers():
    """Sample transformer functions"""
    return {
        "FORMAT_FLOAT": lambda x: f"{float(x):.2f}",
        "UPPERCASE": lambda x: str(x).upper(),
        "FORMAT_CPF": lambda x: f"{str(x)[:3]}.{str(x)[3:6]}.{str(x)[6:9]}-{str(x)[9:11]}",
    }


# ============================================================================
# TEST: FieldBuilder
# ============================================================================


class TestFieldBuilder:
    """Tests for FieldBuilder class"""

    def test_build_direct_field(self):
        """Test building a direct field mapping"""
        builder = FieldBuilder()
        mapping = FieldMapping("nome", "name", "direct")
        source_data = {"nome": "Test Product"}

        target, value = builder.build_field(mapping, source_data)

        assert target == "name"
        assert value == "Test Product"

    def test_build_field_with_transformer(self, transformers):
        """Test field building with transformation"""
        builder = FieldBuilder(transformers)
        mapping = FieldMapping("nome", "name", "direct", transformer="UPPERCASE")
        source_data = {"nome": "test product"}

        target, value = builder.build_field(mapping, source_data)

        assert value == "TEST PRODUCT"

    def test_build_nested_field(self):
        """Test building nested object field"""
        builder = FieldBuilder()
        mapping = FieldMapping("id_marca", "brand", "nested")
        source_data = {"id_marca": 100}

        target, value = builder.build_field(mapping, source_data)

        assert target == "brand"
        assert value == {"id": 100}

    def test_build_array_field(self):
        """Test building array field"""
        builder = FieldBuilder()
        mapping = FieldMapping("id_marca", "brands", "array")
        source_data = {"id_marca": 100}

        target, value = builder.build_field(mapping, source_data)

        assert target == "brands"
        assert value == [{"id": 100}]

    def test_build_attribute_mapping_single(self):
        """Test building a single attribute mapping"""
        builder = FieldBuilder()
        attr_mappings = [
            AttributeMapping("peso", attribute_id=1, attribute_name="Peso", format_string="{value} kg")
        ]
        mapping = FieldMapping("", "attributes", "attribute", attribute_mappings=attr_mappings)
        source_data = {"peso": 2.5}

        target, value = builder.build_field(mapping, source_data)

        assert target == "attributes"
        assert len(value) == 1
        assert value[0]["attribute"]["id"] == 1
        assert value[0]["attribute"]["name"] == "Peso"
        assert value[0]["value"] == "2.5 kg"

    def test_build_attribute_mapping_multiple(self, sample_banco_product):
        """Test building multiple attribute mappings"""
        builder = FieldBuilder()
        attr_mappings = [
            AttributeMapping("peso", attribute_id=1, attribute_name="Peso", format_string="{value} kg"),
            AttributeMapping("altura", attribute_id=2, attribute_name="Altura", format_string="{value} cm"),
            AttributeMapping("largura", attribute_id=3, attribute_name="Largura"),
        ]
        mapping = FieldMapping("", "attributes", "attribute", attribute_mappings=attr_mappings)

        target, value = builder.build_field(mapping, sample_banco_product)

        assert len(value) == 3
        assert value[0]["value"] == "2.5 kg"
        assert value[1]["value"] == "10 cm"
        assert value[2]["value"] == "15"

    def test_attribute_mapping_skip_null(self):
        """Test skip_if_null for attributes"""
        builder = FieldBuilder()
        attr_mappings = [
            AttributeMapping("peso", attribute_id=1, attribute_name="Peso", skip_if_null=True),
            AttributeMapping("altura", attribute_id=2, attribute_name="Altura", skip_if_null=False),
        ]
        mapping = FieldMapping("", "attributes", "attribute", attribute_mappings=attr_mappings)
        source_data = {"peso": None, "altura": None}

        target, value = builder.build_field(mapping, source_data)

        # peso should be skipped
        # altura should be included with empty value
        assert len(value) == 1
        assert value[0]["attribute"]["id"] == 2


# ============================================================================
# TEST: TemplateEngine
# ============================================================================


class TestTemplateEngine:
    """Tests for TemplateEngine class"""

    def test_variable_substitution_simple(self):
        """Test simple variable substitution"""
        engine = TemplateEngine({"name": "Test Product"})
        result = engine.evaluate("Product: ${name}")

        assert result == "Product: Test Product"

    def test_variable_substitution_multiple(self):
        """Test multiple variable substitution"""
        engine = TemplateEngine({"name": "Test", "sku": "SKU123"})
        result = engine.evaluate("${name} (${sku})")

        assert result == "Test (SKU123)"

    def test_variable_substitution_missing(self):
        """Test missing variable returns empty string"""
        engine = TemplateEngine({"name": "Test"})
        result = engine.evaluate("Name: ${name}, Code: ${code}")

        assert "Name: Test" in result
        assert "Code:" in result

    def test_conditional_true(self):
        """Test conditional expression (true case)"""
        engine = TemplateEngine({"premium": True})
        result = engine.evaluate("${if premium ? Premium Product : Standard Product}")

        assert result == "Premium Product"

    def test_conditional_false(self):
        """Test conditional expression (false case)"""
        engine = TemplateEngine({"premium": False})
        result = engine.evaluate("${if premium ? Premium Product : Standard Product}")

        assert result == "Standard Product"

    def test_escape_string(self):
        """Test string escaping"""
        escaped = TemplateEngine.escape_string('Product "Test"\nLine 2')

        assert '\\"' in escaped
        assert '\\n' in escaped


# ============================================================================
# TEST: PayloadBuilder
# ============================================================================


class TestPayloadBuilder:
    """Tests for PayloadBuilder class"""

    def test_build_simple_payload(self, sample_banco_brand):
        """Test building a simple payload"""
        config = PayloadConfig(
            table_name="MARCAS",
            endpoint="/v1/inventory/brands",
            mappings=[
                FieldMapping("nome", "name", "direct"),
                FieldMapping("descricao", "description", "direct"),
            ]
        )

        builder = PayloadBuilder()
        payload = builder.build(config, sample_banco_brand)

        assert payload["name"] == "Michelin"
        assert payload["description"] == "Tire manufacturer"

    def test_build_payload_with_attributes(self, sample_banco_product):
        """Test building payload with attribute mapping"""
        config = PayloadConfig(
            table_name="PRODUTOS",
            endpoint="/v1/catalog/products",
            mappings=[
                FieldMapping("nome", "name", "direct"),
                FieldMapping("sku", "sku", "direct"),
                FieldMapping(
                    source="",
                    target="attributes",
                    type="attribute",
                    attribute_mappings=[
                        AttributeMapping("peso", attribute_id=1, attribute_name="Peso"),
                        AttributeMapping("altura", attribute_id=2, attribute_name="Altura"),
                    ]
                ),
            ]
        )

        builder = PayloadBuilder()
        payload = builder.build(config, sample_banco_product)

        assert payload["name"] == "PNEU 175/60 R15"
        assert "attributes" in payload
        assert len(payload["attributes"]) == 2

    def test_build_batch_payloads(self, sample_banco_product):
        """Test building payloads for multiple rows"""
        config = PayloadConfig(
            table_name="MARCAS",
            endpoint="/v1/inventory/brands",
            mappings=[
                FieldMapping("nome", "name", "direct"),
            ]
        )

        builder = PayloadBuilder()
        rows = [
            {"nome": "Brand 1"},
            {"nome": "Brand 2"},
            {"nome": "Brand 3"},
        ]
        payloads = builder.build_batch(config, rows)

        assert len(payloads) == 3
        assert payloads[0]["name"] == "Brand 1"
        assert payloads[2]["name"] == "Brand 3"

    def test_product_payload_convenience_function(self, sample_banco_product):
        """Test build_product_payload convenience function"""
        payload = build_product_payload(sample_banco_product)

        assert payload["name"] == "PNEU 175/60 R15"
        assert "attributes" in payload
        assert isinstance(payload["attributes"], list)

    def test_brand_payload_convenience_function(self, sample_banco_brand):
        """Test build_brand_payload convenience function"""
        payload = build_brand_payload(sample_banco_brand)

        assert payload["name"] == "Michelin"


# ============================================================================
# TEST: Integration
# ============================================================================


class TestPayloadBuilderIntegration:
    """Integration tests for PayloadBuilder"""

    def test_end_to_end_product_transformation(self, sample_banco_product, transformers):
        """Test complete product transformation from BANCO to Gaud format"""
        # Build payload
        payload = build_product_payload(sample_banco_product, transformers)

        # Verify structure
        assert "name" in payload
        assert "sku" in payload
        assert "attributes" in payload

        # Verify attribute values
        assert len(payload["attributes"]) >= 2

        # Verify each attribute has correct structure
        for attr in payload["attributes"]:
            assert "attribute" in attr
            assert "value" in attr
            assert "id" in attr["attribute"]
            assert "name" in attr["attribute"]

    def test_complex_payload_with_nested_objects(self):
        """Test building payload with multiple nested structures"""
        config = PayloadConfig(
            table_name="PRODUTOS",
            endpoint="/v1/catalog/products",
            mappings=[
                FieldMapping("nome", "name", "direct"),
                FieldMapping("id_marca", "brand", "nested"),
                FieldMapping("id_categoria", "category", "nested"),
            ]
        )

        source_data = {
            "nome": "Product A",
            "id_marca": 100,
            "id_categoria": 50,
        }

        builder = PayloadBuilder()
        payload = builder.build(config, source_data)

        assert payload["name"] == "Product A"
        assert payload["brand"] == {"id": 100}
        assert payload["category"] == {"id": 50}

    def test_attribute_mapping_real_scenario(self):
        """Test attribute mapping with real BANCO.MDB scenario"""
        # Simulate BANCO row with physical dimensions
        banco_row = {
            "id": 1,
            "nome": "Tire XYZ",
            "sku": "TX-001",
            "peso": "2.5",  # Note: might come as string from CSV/Excel
            "altura": "10",
            "largura": "15",
            "profundidade": "20",
            "diametro": None,  # Will be skipped
        }

        config = PayloadConfig(
            table_name="PRODUTOS",
            endpoint="/v1/catalog/products",
            mappings=[
                FieldMapping("nome", "name", "direct"),
                FieldMapping("sku", "sku", "direct"),
                FieldMapping(
                    source="",
                    target="attributes",
                    type="attribute",
                    attribute_mappings=[
                        AttributeMapping("peso", attribute_id=1, attribute_name="Peso", format_string="{value} kg"),
                        AttributeMapping("altura", attribute_id=2, attribute_name="Altura", format_string="{value} cm"),
                        AttributeMapping("largura", attribute_id=3, attribute_name="Largura", format_string="{value} cm"),
                        AttributeMapping("profundidade", attribute_id=4, attribute_name="Profundidade", format_string="{value} cm"),
                        AttributeMapping("diametro", attribute_id=5, attribute_name="Diametro", skip_if_null=True),
                    ]
                ),
            ]
        )

        builder = PayloadBuilder()
        payload = builder.build(config, banco_row)

        # Check output structure
        assert payload["name"] == "Tire XYZ"
        assert payload["sku"] == "TX-001"

        # Check attributes
        attrs = payload["attributes"]
        assert len(attrs) == 4  # diametro skipped (null)

        # Check attribute values are formatted correctly
        peso_attr = next((a for a in attrs if a["attribute"]["id"] == 1), None)
        assert peso_attr is not None
        assert peso_attr["value"] == "2.5 kg"

        altura_attr = next((a for a in attrs if a["attribute"]["id"] == 2), None)
        assert altura_attr is not None
        assert altura_attr["value"] == "10 cm"


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
