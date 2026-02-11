# 🐳 Docker Setup for gaud-erp-migration (Phase 1-2)

Este documento explica como usar Docker para testar a implementação Phase 1-2 da ferramenta gaud-erp-migration.

## 📋 Pré-requisitos

- Docker 20.10+
- Docker Compose 2.0+
- BANCO.MDB (optional, para testes com dados reais)

## 🚀 Quick Start

### 1. Clone/Acesse o repositório

```bash
cd D:\development\gaud\workspace\gaud-erp-migration
```

### 2. Build e Run

```bash
# Build the Docker image
docker-compose build

# Run the container (executa testes automaticamente)
docker-compose up
```

### 3. Acompanhar os testes

O container vai:
1. ✅ Rodar 17 testes Phase 1 (API Introspection)
2. ✅ Rodar 21 testes Phase 2 (PayloadBuilder)
3. ✅ Testar conexão com Gaud API real
4. ✅ Testar transformação end-to-end BANCO → Gaud

Saída esperada:
```
==================================================
gaud-erp-migration Phase 1-2 Docker Environment
==================================================

Running tests...
=== 38 passed in 0.23s ===

Testing Phase 1 with real Gaud API...
SUCCESS: Got schema with 3 endpoints

Testing Phase 1 + Phase 2 integration...
SUCCESS: Phase 1 + Phase 2 integration working perfectly!

==================================================
All tests completed! Container ready for interaction.
==================================================
```

## 📝 Configuração

### Environment Variables

Copie `.env.example` para `.env` e customize:

```bash
cp .env.example .env
```

Edite `.env` com suas credenciais:
```
GAUD_API_URL=https://api-v2.gauderp.com
GAUD_USERNAME=art motos
GAUD_PASSWORD=admin
```

### Volume Configuration

O docker-compose monta:
- `./` → `/workspace` (código-fonte)
- `./.cache/schemas` → `/workspace/.cache/schemas` (schema cache)
- `./data` → `/data` (BANCO.MDB e dados de teste)

## 🧪 Executar Testes Manualmente

### Entrar no container

```bash
docker-compose run --rm migration-tool bash
```

### Rodar testes específicos

```bash
# Todos os testes
python -m pytest -v

# Apenas Phase 1
python -m pytest tests/test_introspection.py -v

# Apenas Phase 2
python -m pytest tests/test_payload_builder.py -v

# Com cobertura
python -m pytest --cov=src tests/
```

### Testar com API real

```bash
# Phase 1: Conexão e descoberta de endpoints
python test_phase1_real_api.py

# Phase 1 + Phase 2: End-to-end BANCO → Gaud
python test_phase1_phase2_integration.py
```

### Rodar CLI (quando Phase 3-4 forem implementadas)

```bash
python main.py
```

## 📂 Estrutura do Container

```
/workspace/
├── src/
│   ├── introspection/    # Phase 1: API Schema Introspection
│   ├── builder/          # Phase 2: Payload Building
│   ├── parser/           # Existing parsers (SQL, CSV, Excel, MDB)
│   ├── mapper/           # Existing mappers
│   └── ...
├── tests/
│   ├── test_introspection.py (17 tests)
│   └── test_payload_builder.py (21 tests)
├── .cache/schemas/       # Schema cache (mounted volume)
├── data/                 # BANCO.MDB and test data (mounted volume)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── main.py
```

## 🔍 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs -f migration-tool

# Rebuild sem cache
docker-compose build --no-cache
```

### Testes falhando

```bash
# Rodar com verbose output
python -m pytest -vv --tb=short

# Ver problemas de importação
python -c "from src.introspection import ApiSchemaIntrospector; print('OK')"
```

### API não responde

```bash
# Verificar conectividade
curl -I https://api-v2.gauderp.com/swagger.json

# Testar com timeout maior
python -c "
from src.introspection import ApiSchemaIntrospector
introspector = ApiSchemaIntrospector(
    api_url='https://api-v2.gauderp.com',
    credentials=('art motos', 'admin'),
    timeout=30
)
schema = introspector.get_schema()
"
```

## 📦 Adicionar BANCO.MDB para Testes

### 1. Crie diretório de dados

```bash
mkdir -p data
```

### 2. Coloque o arquivo

```bash
# Copie BANCO.MDB para ./data/
cp /caminho/para/BANCO.MDB data/
```

### 3. Acesse do container

```bash
# Dentro do container, o arquivo estará em:
ls /data/BANCO.MDB
```

### 4. Rodar testes com dados reais

```bash
# (implementado em Phase 3-4)
python main.py --input /data/BANCO.MDB
```

## 🎯 Próximos Passos

Com Phase 1-2 testado no Docker, próximos passos:

1. **Phase 3: RelationshipResolver** (10h)
   - Implementar resolução de FK com 3-level fallback
   - Integrar com getOrCreate endpoints (já implementados)
   - Adicionar testes

2. **Phase 4: ExecutionOrchestrator** (10h)
   - Implementar orquestração de chamadas API
   - Batch processing com SSE streaming
   - Gerar relatórios de migração

3. **End-to-End Testing**
   - Testar com BANCO.MDB real
   - Validar payloads contra Gaud API
   - Verificar dados importados

## 📖 Documentação Relacionada

- `IMPLEMENTATION_STATUS.md` - Status completo Phase 1-2
- `gaud-erp-migration-evolution.md` - Arquitetura completa
- `src/introspection/api_schema_introspector.py` - Phase 1 code
- `src/builder/payload_builder.py` - Phase 2 code

## 💬 Comandos Úteis

```bash
# Build
docker-compose build

# Run (com testes automáticos)
docker-compose up

# Run interativo (bash)
docker-compose run --rm migration-tool bash

# Ver logs
docker-compose logs -f migration-tool

# Parar container
docker-compose down

# Limpar tudo (volume include)
docker-compose down -v

# Re-build após mudanças no código
docker-compose up --build
```

## ✅ Validação Checklist

Antes de usar em produção:

- [ ] Docker build completa sem erros
- [ ] 38/38 testes passando
- [ ] Conexão com Gaud API real OK
- [ ] E2E BANCO → Gaud funcionando
- [ ] Schema cache criado
- [ ] Transformações com AttributeMapping OK
- [ ] Payloads nested structures validadas

---

**Status**: ✅ Ready for Phase 1-2 Testing
**Last Updated**: 2026-02-11
