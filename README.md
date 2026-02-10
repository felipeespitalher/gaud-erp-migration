# GAUD ERP Migration Tool

Local CLI tool para migração de dados de clientes para o Gaud ERP.

## Features

- ✅ Parser de SQL dumps
- ✅ Auto-discovery de schema
- ✅ Auto-mapeamento inteligente (com heurísticas)
- ✅ Suporte a mapeamentos N→1 e 1→N
- ✅ Validação de dados pré-import
- ✅ Transformadores built-in (CPF, CNPJ, datas, telefone, etc)
- ✅ Export JSON
- ✅ Integração com gaud-erp-api via endpoints
- ✅ Cache local de schema Gaud

## Quick Start

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar ferramenta
python main.py

# Com arquivo direto (não-interativo)
python main.py --backup backup/customer.sql

# Rodar testes
pytest tests/ -v
```

## Fluxo de Uso

1. **Sincronizar Schema**: Baixa schema do Gaud (cacheado localmente)
2. **Upload Backup**: Seleciona arquivo .sql do cliente
3. **Analisar**: Descobre schema do backup
4. **Auto-Map**: Sugere mapeamentos automáticos
5. **Editar**: Ajusta mapeamentos conforme necessário
6. **Validar**: Valida dados pré-import
7. **Export**: Gera JSON pronto para import
8. **Import**: Envia dados para gaud-erp-api

## Estrutura do Projeto

```
src/
├── cli/                  # Interface de linha de comando
├── parser/              # Parsers (SQL, CSV, JSON)
├── schema/              # Descoberta e modelos de schema
├── mapper/              # Mapeamento de tabelas/colunas
├── transformer/         # Transformações de dados
├── validator/           # Validação de dados
├── exporter/            # Exportação (JSON, CSV, HTML)
├── api/                 # Client HTTP para gaud-erp-api
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
