# 🧪 Tests - Aconex RAG System

Esta carpeta contiene todos los tests automatizados del sistema RAG de Aconex.

## 📁 Estructura

```
tests/
├── __init__.py              # Package marker
├── conftest.py              # Fixtures y configuración compartida
├── test_ingest.py           # Tests de ingesta de documentos
├── test_search.py           # Tests de búsqueda semántica
├── test_upload.py           # Tests de carga de archivos
├── test_utils.py            # Tests de utilidades
└── test_api.py              # Tests de endpoints API
```

## 🚀 Quick Start

### Ejecutar todos los tests
```powershell
pytest tests/ -v
```

### Ejecutar con cobertura
```powershell
pytest tests/ --cov=app --cov-report=html
```

### Usar el script helper
```powershell
.\run_tests.ps1 cov
```

## 📊 Cobertura de Tests

| Módulo | Tests | Cobertura Objetivo |
|--------|-------|-------------------|
| `app/ingest.py` | 25+ tests | >= 85% |
| `app/search_core.py` | 20+ tests | >= 90% |
| `app/upload.py` | 18+ tests | >= 80% |
| `app/utils.py` | 15+ tests | >= 95% |
| `app/api.py` | 25+ tests | >= 75% |
| **TOTAL** | **100+ tests** | **>= 80%** |

## 🎯 Categorías de Tests

### Por Markers

- `@pytest.mark.unit` - Tests unitarios (funciones aisladas)
- `@pytest.mark.integration` - Tests de integración (múltiples componentes)
- `@pytest.mark.api` - Tests de endpoints REST
- `@pytest.mark.db` - Tests que requieren base de datos
- `@pytest.mark.mock` - Tests que usan mocks extensivamente
- `@pytest.mark.slow` - Tests que toman > 1 segundo

### Ejecutar por categoría

```powershell
pytest tests/ -m "unit" -v          # Solo unitarios
pytest tests/ -m "integration" -v   # Solo integración
pytest tests/ -m "api" -v           # Solo API
```

## 🛠️ Fixtures Disponibles

Ver `conftest.py` para la lista completa. Principales:

- `test_env_vars` - Variables de entorno para tests
- `mock_db_connection` - Mock de PostgreSQL
- `mock_sentence_transformer` - Mock del modelo de embeddings
- `sample_aconex_document` - Documento Aconex de prueba
- `test_client` - Cliente FastAPI para tests

## 📖 Documentación

- [TESTING_STRATEGY.md](../TESTING_STRATEGY.md) - Estrategia completa
- [TESTING_GUIDE.md](../TESTING_GUIDE.md) - Guía de ejecución
- [requirements-test.txt](../requirements-test.txt) - Dependencias

## 🔍 Escenarios Cubiertos

### ✅ Ingesta (test_ingest.py)
- Lectura de JSON/NDJSON
- Normalización de documentos Aconex
- Generación de embeddings
- Inserción en BD
- Deduplicación
- Flujo completo end-to-end

### ✅ Búsqueda (test_search.py)
- Búsqueda vectorial básica
- Filtros por project_id
- Ranking híbrido
- Threshold de relevancia
- Casos edge (queries vacíos, caracteres especiales)

### ✅ Upload (test_upload.py)
- Extracción de texto (PDF, TXT, DOCX, JSON)
- Chunking adaptativo
- Ingesta en tiempo real
- Detección de duplicados
- Almacenamiento de file_content

### ✅ API (test_api.py)
- POST /search
- POST /chat
- POST /upload
- GET /health
- GET /document/{id}/file
- Manejo de errores
- Validación de parámetros

### ✅ Utilidades (test_utils.py)
- Conexión a BD
- Chunking de texto
- Manejo de configuración

## 💡 Tips

### Durante Desarrollo
```powershell
# Parar en el primer error
pytest tests/ -x -v

# Ver prints en tests
pytest tests/ -s -v

# Test específico
pytest tests/test_ingest.py::test_normalize_doc_complete -v
```

### Antes de Commit
```powershell
# Verificar todo
.\run_tests.ps1 cov

# O manualmente
pytest tests/ --cov=app --cov-fail-under=80
```

### CI/CD
```powershell
pytest tests/ --cov=app --cov-report=xml --junit-xml=test-results.xml
```

## 🐛 Troubleshooting

**Error: No module named 'app'**
```powershell
# Asegúrate de estar en backend-acorag/
cd backend-acorag
pytest tests/ -v
```

**Tests muy lentos**
```powershell
# Ejecutar en paralelo
pytest tests/ -n auto
```

**Ver solo tests fallidos**
```powershell
pytest tests/ --lf -v
```

## 📈 Métricas de Calidad

- ✅ **100+ tests** automatizados
- ✅ **>= 80%** cobertura de código
- ✅ **< 2 minutos** tiempo total de ejecución
- ✅ **0 warnings** en ejecución limpia
- ✅ **Todos los escenarios críticos** cubiertos

## 🤝 Contribuir

Al agregar nuevas funcionalidades:

1. Escribe tests ANTES de implementar (TDD)
2. Usa fixtures existentes cuando sea posible
3. Marca los tests con decoradores apropiados
4. Verifica que la cobertura no baje
5. Documenta escenarios edge cases

---

**Última actualización:** 2025-11-24  
**Versión:** 1.0
