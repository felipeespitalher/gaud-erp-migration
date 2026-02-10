# GAUD ERP Migration Tool

Local CLI tool interativo para migração de dados de clientes para o Gaud ERP.

**Status**: Phase 2 ✅ Completo | **Python 3.10+** | **MIT License**

## Features

### Parsers & Formatos Suportados
- ✅ SQL dumps (PostgreSQL, MySQL, Oracle, Firebird) - com dialect detection automático
- ✅ CSV files - auto-detecção de separador (`,;|` ou tab), type inference
- ✅ Excel files - multi-sheet support, type inference por sheet
- ✅ Microsoft Access - suporte `.mdb` e `.accdb`
- ✅ JSON (em progresso)

### Análise & Mapeamento
- ✅ Auto-discovery de schema inteligente
- ✅ Auto-mapeamento com heurísticas (fuzzy matching)
- ✅ Suporte a mapeamentos N→1 e 1→N
- ✅ TableSelector interativo - escolha exatamente quais tabelas importar
- ✅ Validação de dados pré-import

### Transformação & Integração
- ✅ Transformadores built-in (CPF, CNPJ, datas, uppercase, trim, etc)
- ✅ EndpointMapper - mapeia tabelas para endpoints da API
- ✅ DataImporter - importa via endpoints reais (NÃO raw data blobs)
- ✅ Export JSON com schema e mappings
- ✅ Cache local de schema Gaud

### Desenvolvimento
- ✅ Testes unitários (18 passed, 1 skipped)
- ✅ Poetry para dependency management
- ✅ CLI com Click framework
- ✅ Logging estruturado com colorama

## Installation

### Option 1: Poetry (Recomendado)

```bash
# Instalar Poetry
pip install poetry

# Instalar dependências
poetry install

# Executar ferramenta
poetry run python main.py

# Rodar testes
poetry run pytest tests/ -v
```

### Option 2: Pip

```bash
# Criar virtual environment
python -m venv venv
source venv/bin/activate  # no Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar ferramenta
python main.py

# Rodar testes
pytest tests/ -v
```

## Quick Start

```bash
# Menu interativo
python main.py

# Sincronizar schema do Gaud
python main.py

# Com arquivo de backup específico
python main.py migrate /path/to/backup.csv

# Rodar testes
pytest tests/ -v --cov=src
```

## Fluxo de Uso (Phase 2)

```
┌─────────────────────────────────────────────────────────┐
│  Step 0: Parse Backup File                              │
│  └─ Auto-detects format: SQL, CSV, Excel, Access        │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Step 1: Interactive Table Selection                    │
│  └─ Choose which tables to import (not all!)            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Step 2: Auto-Mapping                                   │
│  └─ Heuristic matcher: customers ↔ /v1/customers       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Step 3: Interactive Mapping Review                     │
│  └─ Edit mappings or mark tables as SKIP                │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Step 4: Validate Mappings                              │
│  └─ Ensure all tables have endpoints                    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Step 5: Import via API Endpoints                       │
│  └─ POST /v1/customers, /v1/products, etc (NOT raw)    │
│  └─ Batch processing + error handling                   │
└─────────────────────────────────────────────────────────┘
```

### Arquitetura Crítica

**❌ ERRADO (não fazemos mais isso):**
```
POST /v1/migration/import { data: {...} }  # Raw blob
```

**✅ CORRETO (Phase 2):**
```
POST /v1/customers { records: [...] }
POST /v1/products { records: [...] }
POST /v1/orders { records: [...] }
```

## Parsers Suportados (Phase 2)

### SQL Dumps
```bash
python main.py
# Seleciona arquivo .sql
# Auto-detects: PostgreSQL, MySQL, Oracle, Firebird
```

### CSV Files
```bash
python main.py
# Seleciona arquivo .csv
# Auto-detecta separador: , ; | ou \t
# Infere tipos: INTEGER, FLOAT, DATE, VARCHAR
```

### Excel Files
```bash
python main.py
# Seleciona arquivo .xlsx ou .xls
# Suporta múltiplas abas
# Cada aba = 1 tabela
# Type inference automático
```

### Microsoft Access
```bash
python main.py
# Seleciona arquivo .mdb ou .accdb
# Extrai todas as tabelas
# Preserva metadados
```

## EndpointMapper Examples

```python
# Exact matches
customers    → /v1/customers
orders       → /v1/orders
invoices     → /v1/invoices
payments     → /v1/payments

# Fuzzy matches (70%+ confidence)
client       → /v1/customers
produto      → /v1/products
pedido       → /v1/orders
nfe          → /v1/invoices

# Table name cleaning
tb_customers → /v1/customers
tbl_products_data → /v1/products
src_orders   → /v1/orders
```

## Estrutura do Projeto

```
src/
├── cli/                  # CLI interativa com Click
│   ├── interactive.py    # Loop principal e orquestração
│   └── table_selector.py # Seleção interativa de tabelas
├── parser/              # Parsers multi-formato (Phase 2)
│   ├── backup_parser.py # Interface abstrata
│   ├── parser_factory.py # Factory pattern
│   ├── sql_parser.py    # SQL dumps (PostgreSQL, MySQL, Oracle, Firebird)
│   ├── csv_parser.py    # CSV com auto-detect separator
│   ├── excel_parser.py  # Excel com openpyxl
│   └── access_parser.py # Access MDB/ACCDB
├── api/                 # Integração com gaud-erp-api (Phase 2)
│   ├── gaud_client.py   # HTTP client
│   ├── endpoint_mapper.py # Mapeia tabelas → endpoints
│   └── data_importer.py # Importa via endpoints reais
├── schema/              # Modelos de schema
├── mapper/              # Mapeamento de tabelas/colunas
├── transformer/         # Transformações de dados
├── validator/           # Validação de dados
├── exporter/            # Exportação (JSON)
└── utils/               # Utilities
```

## Arquivo de Configuração

`config/gaud_schema.json` - Cache do schema Gaud (criado automaticamente)

## Desenvolvimento

```bash
# Instalar dev dependencies
pip install -r requirements.txt

# Rodar linter
black src/
flake8 src/

# Type checking
mypy src/

# Testes com cobertura
pytest tests/ --cov=src
```
