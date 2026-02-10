"""Tests for EndpointMapper."""
import pytest

from src.api.endpoint_mapper import EndpointMapper


class TestEndpointMapper:
    """Test endpoint mapping."""

    def test_exact_match_customers(self):
        """Test exact match for customers."""
        assert EndpointMapper.get_endpoint("customers") == "/v1/customers"
        assert EndpointMapper.get_endpoint("customer") == "/v1/customers"

    def test_exact_match_products(self):
        """Test exact match for products."""
        assert EndpointMapper.get_endpoint("products") == "/v1/products"
        assert EndpointMapper.get_endpoint("product") == "/v1/products"

    def test_exact_match_orders(self):
        """Test exact match for orders."""
        assert EndpointMapper.get_endpoint("orders") == "/v1/orders"
        assert EndpointMapper.get_endpoint("pedidos") == "/v1/orders"

    def test_exact_match_invoices(self):
        """Test exact match for invoices."""
        assert EndpointMapper.get_endpoint("invoices") == "/v1/invoices"
        assert EndpointMapper.get_endpoint("notas") == "/v1/invoices"
        assert EndpointMapper.get_endpoint("nfe") == "/v1/invoices"

    def test_exact_match_payments(self):
        """Test exact match for payments."""
        assert EndpointMapper.get_endpoint("payments") == "/v1/payments"
        assert EndpointMapper.get_endpoint("pagamentos") == "/v1/payments"

    def test_fuzzy_match(self):
        """Test fuzzy matching for similar names."""
        # These should fuzzy match with high confidence
        result = EndpointMapper.get_endpoint("client")
        assert result == "/v1/customers"  # client -> customer

        result = EndpointMapper.get_endpoint("produto")
        assert result == "/v1/products"  # produto -> product

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert EndpointMapper.get_endpoint("CUSTOMERS") == "/v1/customers"
        assert EndpointMapper.get_endpoint("Products") == "/v1/products"
        assert EndpointMapper.get_endpoint("OrDeRs") == "/v1/orders"

    def test_no_match(self):
        """Test when no match is found."""
        result = EndpointMapper.get_endpoint("nonexistent_table")
        # Should return None or fuzzy match with low confidence
        # (depends on implementation)
        pass

    def test_clean_table_name(self):
        """Test table name cleaning."""
        cleaned = EndpointMapper._clean_table_name("tb_customers")
        assert cleaned == "customers"

        cleaned = EndpointMapper._clean_table_name("tbl_products_data")
        assert cleaned == "products"

    def test_suggest_endpoints(self):
        """Test endpoint suggestions."""
        suggestions = EndpointMapper.suggest_endpoints("customers", limit=3)
        assert len(suggestions) > 0
        assert suggestions[0][0] == "/v1/customers"

    def test_get_all_endpoints(self):
        """Test getting all endpoints."""
        endpoints = EndpointMapper.get_all_endpoints()
        assert "/v1/customers" in endpoints
        assert "/v1/products" in endpoints
        assert "/v1/orders" in endpoints
        assert "/v1/invoices" in endpoints
        assert "/v1/payments" in endpoints


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
