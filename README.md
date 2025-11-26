# Aconex RAG Starter (mínimo)

## 🚀 Quick Start

Sigue estos pasos:
1) docker compose up -d
2) psql $DATABASE_URL -f sql/schema.sql && psql $DATABASE_URL -f sql/indexes.sql
3) python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
4) python app/ingest.py --json_path data/aconex_emails.json --project_id PROYECTO_001
5) uvicorn app.server:app --host 0.0.0.0 --port 8000

---

## 🧪 Testing

### **Estado Actual: 9/9 Tests Pasando (100%)**

Suite de tests simplificada enfocada en funcionalidad core del sistema RAG.

#### **Ejecutar Tests**
```powershell
# Todos los tests
pytest tests/ -v

# Por módulo
pytest tests/test_ingest.py -v    # Ingesta de documentos
pytest tests/test_search.py -v    # Búsqueda semántica
pytest tests/test_upload.py -v    # Upload en tiempo real
pytest tests/test_utils.py -v     # Utilidades core

# Con cobertura
pytest tests/ --cov=app --cov-report=html
```

#### **📚 Documentación de Tests**

| Documento | Descripción |
|-----------|-------------|
| **[DOCUMENTACION_TESTS.md](DOCUMENTACION_TESTS.md)** | 📋 Documentación completa de tests (pasando y fallidos) |
| **[ERRORES_Y_SOLUCIONES_TESTS.md](ERRORES_Y_SOLUCIONES_TESTS.md)** | 🐛 Registro detallado de errores y soluciones |
| **[TESTING_GUIDE.md](TESTING_GUIDE.md)** | 🧪 Guía de ejecución de tests |
| **[TESTING_SUMMARY.md](TESTING_SUMMARY.md)** | 📊 Resumen ejecutivo del proyecto de testing |

#### **Escenarios Cubiertos**
- ✅ **Ingesta de Documentos**: Normalización Aconex, parsing JSON/NDJSON
- ✅ **Búsqueda Semántica**: Vector search, multi-tenancy, ranking híbrido
- ✅ **Upload en Tiempo Real**: Extracción TXT, generación de IDs determinísticos
- ✅ **Utilidades Core**: Chunking con overlap, conexión BD, casos borde

---

## 📖 Documentación Adicional
