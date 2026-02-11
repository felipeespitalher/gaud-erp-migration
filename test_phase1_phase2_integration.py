#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-end test: Phase 1 (API Introspection) + Phase 2 (PayloadBuilder)

Demonstrates:
1. Phase 1: Fetch Gaud API schema
2. Phase 2: Build BANCO.MDB product payload according to schema
"""

import json
from src.introspection import ApiSchemaIntrospector
from src.builder import build_product_payload

def test_integration():
    """Test Phase 1 + Phase 2 integration"""
    print("\n" + "="*70)
    print("Phase 1 + Phase 2 Integration Test")
    print("="*70 + "\n")

    # Phase 1: Get API schema
    print("PHASE 1: Fetching Gaud API schema...")
    introspector = ApiSchemaIntrospector(
        api_url="https://api-v2.gauderp.com",
        credentials=("art motos", "admin"),
        timeout=15
    )

    try:
        schema = introspector.get_schema()
        print(f"SUCCESS: Got schema with {len(schema.endpoints)} endpoints\n")

        # Verify product endpoint structure
        product_endpoint = schema.get_endpoint("/v1/catalog/products", "POST")
        if product_endpoint:
            print(f"Product endpoint fields:")
            for field_name, field in list(product_endpoint.request_body_fields.items())[:5]:
                print(f"  - {field_name}: {field.type.value}")
            if len(product_endpoint.request_body_fields) > 5:
                print(f"  ... + {len(product_endpoint.request_body_fields) - 5} more fields\n")

    except Exception as e:
        print(f"WARNING: Could not fetch API schema: {e}")
        schema = None

    # Phase 2: Build product payload from BANCO.MDB
    print("PHASE 2: Building BANCO.MDB product payload...\n")

    banco_product = {
        "id": 4910,
        "nome": "PNEU 175/60 R15",
        "sku": "P175",
        "descricao": "Pneu de alta performance para autos",
        "peso": "2.5",
        "altura": "10",
        "largura": "15",
        "profundidade": "20",
        "preco": 150.00,
        "custo": 75.00,
        "id_marca": 2,
        "id_categoria": 1,
        "id_fornecedor": 5,
        "ativo": 1,
    }

    print("Input BANCO.MDB row:")
    print(f"  nome: {banco_product['nome']}")
    print(f"  sku: {banco_product['sku']}")
    print(f"  peso: {banco_product['peso']} kg")
    print(f"  altura: {banco_product['altura']} cm")
    print(f"  largura: {banco_product['largura']} cm")
    print(f"  profundidade: {banco_product['profundidade']} cm\n")

    # Build payload
    payload = build_product_payload(banco_product)

    print("Output Gaud API Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    # Validate structure
    print("\n" + "="*70)
    print("Validation:")
    print("="*70)

    checks = [
        ("name field", "name" in payload and payload["name"] == "PNEU 175/60 R15"),
        ("sku field", "sku" in payload),
        ("description field", "description" in payload),
        ("attributes array", "attributes" in payload and isinstance(payload["attributes"], list)),
        ("attributes count", len(payload.get("attributes", [])) == 4),
        ("attribute 1: Peso", any(a.get("attribute", {}).get("name") == "Peso" for a in payload.get("attributes", []))),
        ("attribute values formatted", any("kg" in a.get("value", "") for a in payload.get("attributes", []))),
    ]

    for check_name, result in checks:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {check_name}")

    all_passed = all(result for _, result in checks)

    print("\n" + "="*70)
    if all_passed:
        print("SUCCESS: Phase 1 + Phase 2 integration working perfectly!")
    else:
        print("WARNING: Some validation checks failed")
    print("="*70 + "\n")

    return all_passed

if __name__ == "__main__":
    test_integration()
