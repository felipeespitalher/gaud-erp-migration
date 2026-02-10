"""Map source database tables to gaud-erp-api endpoints."""
from typing import Optional
from difflib import SequenceMatcher


class EndpointMapper:
    """Maps source tables to gaud-erp-api endpoints."""

    # Mapping of common table names to API endpoints
    MAPPING = {
        # Customers
        'customers': '/v1/customers',
        'customer': '/v1/customers',
        'client': '/v1/customers',
        'clients': '/v1/customers',
        'pessoa': '/v1/customers',
        'pessoas': '/v1/customers',
        'contato': '/v1/customers',
        'contatos': '/v1/customers',

        # Products
        'products': '/v1/products',
        'product': '/v1/products',
        'item': '/v1/products',
        'items': '/v1/products',
        'produto': '/v1/products',
        'produtos': '/v1/products',
        'sku': '/v1/products',

        # Orders
        'orders': '/v1/orders',
        'order': '/v1/orders',
        'pedido': '/v1/orders',
        'pedidos': '/v1/orders',
        'venda': '/v1/orders',
        'vendas': '/v1/orders',

        # Invoices
        'invoices': '/v1/invoices',
        'invoice': '/v1/invoices',
        'nota': '/v1/invoices',
        'notas': '/v1/invoices',
        'nfe': '/v1/invoices',
        'fiscal': '/v1/invoices',

        # Payments
        'payments': '/v1/payments',
        'payment': '/v1/payments',
        'pagamento': '/v1/payments',
        'pagamentos': '/v1/payments',
        'recebimento': '/v1/payments',
        'recebimentos': '/v1/payments',

        # Suppliers
        'suppliers': '/v1/suppliers',
        'supplier': '/v1/suppliers',
        'fornecedor': '/v1/suppliers',
        'fornecedores': '/v1/suppliers',

        # Stock/Inventory
        'inventory': '/v1/inventory',
        'stock': '/v1/inventory',
        'estoque': '/v1/inventory',
        'estoques': '/v1/inventory',

        # Categories
        'categories': '/v1/categories',
        'category': '/v1/categories',
        'categoria': '/v1/categories',
        'categorias': '/v1/categories',
    }

    @staticmethod
    def get_endpoint(table_name: str) -> Optional[str]:
        """
        Get endpoint for a table name.

        Uses exact match first, then fuzzy matching for high confidence.

        Args:
            table_name: Source table name

        Returns:
            str: API endpoint path, or None if no mapping found
        """
        if not table_name:
            return None

        table_lower = table_name.lower().strip()

        # Exact match
        if table_lower in EndpointMapper.MAPPING:
            return EndpointMapper.MAPPING[table_lower]

        # Try removing common prefixes/suffixes
        cleaned = EndpointMapper._clean_table_name(table_lower)
        if cleaned in EndpointMapper.MAPPING:
            return EndpointMapper.MAPPING[cleaned]

        # Fuzzy match with high confidence
        best_match = None
        best_score = 0

        for key, endpoint in EndpointMapper.MAPPING.items():
            similarity = SequenceMatcher(None, table_lower, key).ratio()
            if similarity > best_score and similarity >= 0.7:  # 70% confidence threshold
                best_score = similarity
                best_match = endpoint

        return best_match

    @staticmethod
    def _clean_table_name(table_name: str) -> str:
        """
        Clean table name by removing common prefixes/suffixes.

        Args:
            table_name: Table name (lowercase)

        Returns:
            str: Cleaned table name
        """
        # Remove common prefixes
        prefixes = ['tb_', 'tbl_', 'src_', 'dst_', 'tmp_', 'v_', 't_']
        for prefix in prefixes:
            if table_name.startswith(prefix):
                table_name = table_name[len(prefix):]

        # Remove common suffixes
        suffixes = ['_data', '_info', '_detail', '_details', '_list', '_log']
        for suffix in suffixes:
            if table_name.endswith(suffix):
                table_name = table_name[:-len(suffix)]

        return table_name

    @staticmethod
    def get_all_endpoints() -> list:
        """
        Get list of all supported endpoints.

        Returns:
            list: Unique endpoints
        """
        return sorted(list(set(EndpointMapper.MAPPING.values())))

    @staticmethod
    def suggest_endpoints(table_name: str, limit: int = 5) -> list:
        """
        Suggest possible endpoints for a table name.

        Args:
            table_name: Source table name
            limit: Maximum number of suggestions

        Returns:
            list: List of (endpoint, confidence) tuples, sorted by confidence
        """
        if not table_name:
            return []

        table_lower = table_name.lower().strip()
        suggestions = []

        for key, endpoint in EndpointMapper.MAPPING.items():
            similarity = SequenceMatcher(None, table_lower, key).ratio()
            if similarity >= 0.6:  # 60% threshold for suggestions
                suggestions.append((endpoint, similarity, key))

        # Sort by score descending
        suggestions.sort(key=lambda x: x[1], reverse=True)

        # Return top N unique endpoints
        seen = set()
        result = []
        for endpoint, score, key in suggestions:
            if endpoint not in seen:
                result.append((endpoint, f"{score:.1%}"))
                seen.add(endpoint)
                if len(result) >= limit:
                    break

        return result
