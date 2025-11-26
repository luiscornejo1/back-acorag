# 🧪 Estrategia de Testing - Aconex RAG System

## 📊 Resumen Ejecutivo

Este documento define la estrategia completa de testing para el sistema RAG de Aconex, incluyendo todos los escenarios críticos, cobertura esperada y mejores prácticas.

---

## 🎯 Objetivos de Testing

1. **Cobertura >= 80%** de las funciones críticas del core
2. **Tests unitarios** para funciones individuales
3. **Tests de integración** para flujos completos
4. **Tests de API** para endpoints REST
5. **Mocks efectivos** para dependencias externas (BD, modelos, APIs)

---

## 📋 Escenarios de Testing

### 1️⃣ **Escenario de Ingesta** (`test_ingest.py`)

**Componentes bajo prueba:** `app/ingest.py`

**Casos de prueba:**

#### A. Lectura de Archivos
- ✅ `test_iter_docs_from_file_json_list()` - Leer array JSON
- ✅ `test_iter_docs_from_file_json_single()` - Leer objeto JSON único
- ✅ `test_iter_docs_from_file_ndjson()` - Leer NDJSON (línea por línea)
- ✅ `test_iter_docs_from_file_invalid()` - Manejar archivos inválidos

#### B. Normalización de Documentos
- ✅ `test_normalize_doc_complete()` - Documento con todos los campos
- ✅ `test_normalize_doc_minimal()` - Documento con campos mínimos
- ✅ `test_normalize_doc_missing_fields()` - Documento con campos faltantes
- ✅ `test_normalize_doc_date_parsing()` - Parseo de fechas ISO
- ✅ `test_normalize_doc_full_text_priority()` - Priorizar full_text si existe

#### C. Operaciones de BD
- ✅ `test_upsert_documents()` - Inserción/actualización de documentos
- ✅ `test_upsert_documents_conflict()` - Manejo de conflictos (ON CONFLICT)
- ✅ `test_insert_doc_chunks()` - Inserción de chunks con embeddings
- ✅ `test_dedupe_by_key()` - Deduplicación por document_id

#### D. Embeddings
- ✅ `test_stable_chunk_id()` - IDs deterministas para chunks
- ✅ `test_get_model_dim()` - Obtener dimensión del modelo
- ✅ `test_load_model()` - Carga del modelo de embeddings

#### E. Flujo Completo
- ✅ `test_main_ingestion_flow()` - Flujo end-to-end de ingesta

---

### 2️⃣ **Escenario de Embeddings** (`test_embeddings.py`)

**Componentes bajo prueba:** Modelos de SentenceTransformer

**Casos de prueba:**

#### A. Generación de Embeddings
- ✅ `test_embedding_generation()` - Generar embeddings para textos
- ✅ `test_embedding_normalization()` - Verificar normalización L2
- ✅ `test_embedding_dimension()` - Dimensión correcta (384 para MiniLM)
- ✅ `test_embedding_consistency()` - Mismo texto = mismo embedding

#### B. Similitud Semántica
- ✅ `test_semantic_similarity_high()` - Textos similares
- ✅ `test_semantic_similarity_low()` - Textos diferentes
- ✅ `test_batch_encoding()` - Encodificar múltiples textos

---

### 3️⃣ **Escenario de Búsqueda** (`test_search.py`)

**Componentes bajo prueba:** `app/search_core.py`

**Casos de prueba:**

#### A. Búsqueda Básica
- ✅ `test_semantic_search_basic()` - Búsqueda sin filtros
- ✅ `test_semantic_search_with_project()` - Filtrar por project_id
- ✅ `test_semantic_search_top_k()` - Limitar resultados (top_k)
- ✅ `test_semantic_search_no_results()` - Query sin coincidencias

#### B. Ranking y Relevancia
- ✅ `test_search_ranking_order()` - Resultados ordenados por score
- ✅ `test_search_threshold_filter()` - Filtrar por threshold mínimo
- ✅ `test_hybrid_scoring()` - Score híbrido (vector + texto)

#### C. Búsqueda de Texto Completo
- ✅ `test_text_search_title()` - Búsqueda en títulos
- ✅ `test_text_search_number()` - Búsqueda por número de documento
- ✅ `test_text_search_content()` - Búsqueda en contenido

#### D. Casos Edge
- ✅ `test_search_empty_query()` - Query vacío
- ✅ `test_search_special_characters()` - Caracteres especiales
- ✅ `test_search_very_long_query()` - Query muy largo

---

### 4️⃣ **Escenario de Chat/RAG** (`test_chat.py`)

**Componentes bajo prueba:** Endpoint `/chat` en `app/api.py`

**Casos de prueba:**

#### A. Generación de Respuestas
- ✅ `test_chat_basic_question()` - Pregunta básica
- ✅ `test_chat_with_context()` - Respuesta basada en documentos
- ✅ `test_chat_no_relevant_docs()` - Sin documentos relevantes
- ✅ `test_chat_with_history()` - Conversación con historial

#### B. Contexto y Fuentes
- ✅ `test_chat_context_construction()` - Construcción de contexto
- ✅ `test_chat_sources_included()` - Fuentes incluidas en respuesta
- ✅ `test_chat_max_context_docs()` - Límite de documentos de contexto

#### C. Detección de Preguntas Irrelevantes
- ✅ `test_chat_irrelevant_question()` - Detectar preguntas fuera de scope
- ✅ `test_chat_low_score_threshold()` - Threshold de relevancia bajo

#### D. Integración con LLM
- ✅ `test_chat_with_groq()` - Respuesta con Groq API (mock)
- ✅ `test_chat_without_groq()` - Fallback sin Groq

---

### 5️⃣ **Escenario de Upload** (`test_upload.py`)

**Componentes bajo prueba:** `app/upload.py`

**Casos de prueba:**

#### A. Extracción de Texto
- ✅ `test_extract_text_pdf()` - Extraer de PDF
- ✅ `test_extract_text_txt()` - Extraer de TXT
- ✅ `test_extract_text_docx()` - Extraer de DOCX
- ✅ `test_extract_text_json()` - Extraer de JSON

#### B. Chunking
- ✅ `test_chunk_text_small()` - Texto menor a chunk_size
- ✅ `test_chunk_text_large()` - Texto grande (múltiples chunks)
- ✅ `test_chunk_text_overlap()` - Verificar overlap entre chunks

#### C. Ingesta de Documentos
- ✅ `test_ingest_document_complete()` - Ingesta completa
- ✅ `test_ingest_document_duplicate()` - Detectar duplicados
- ✅ `test_generate_document_id()` - ID único por documento

#### D. API de Upload
- ✅ `test_upload_endpoint_pdf()` - POST /upload con PDF
- ✅ `test_upload_endpoint_invalid_type()` - Archivo no soportado
- ✅ `test_upload_and_query_endpoint()` - POST /upload-and-query

---

### 6️⃣ **Escenario de Autenticación** (`test_auth.py`)

**Componentes bajo prueba:** `app/auth.py` y endpoints de auth

**Casos de prueba:**

#### A. Registro
- ✅ `test_register_new_user()` - Registrar usuario nuevo
- ✅ `test_register_duplicate_email()` - Email ya registrado
- ✅ `test_register_invalid_email()` - Email inválido

#### B. Login
- ✅ `test_login_success()` - Login exitoso
- ✅ `test_login_wrong_password()` - Contraseña incorrecta
- ✅ `test_login_nonexistent_user()` - Usuario no existe

#### C. JWT Tokens
- ✅ `test_create_access_token()` - Crear token
- ✅ `test_verify_token()` - Verificar token válido
- ✅ `test_expired_token()` - Token expirado
- ✅ `test_invalid_token()` - Token inválido

#### D. Protección de Endpoints
- ✅ `test_protected_endpoint_with_token()` - Acceso con token
- ✅ `test_protected_endpoint_without_token()` - Acceso sin token

---

### 7️⃣ **Escenario de Utilidades** (`test_utils.py`)

**Componentes bajo prueba:** `app/utils.py`

**Casos de prueba:**

#### A. Conexión a BD
- ✅ `test_get_db_connection()` - Obtener conexión
- ✅ `test_db_connection_missing_env()` - DATABASE_URL no configurada

#### B. Chunking
- ✅ `test_simple_chunk_small_text()` - Texto pequeño
- ✅ `test_simple_chunk_large_text()` - Texto grande
- ✅ `test_simple_chunk_with_overlap()` - Overlap configurado
- ✅ `test_simple_chunk_edge_cases()` - Casos edge (texto vacío, etc.)

---

## 🛠️ Herramientas y Configuración

### Dependencias de Testing

```bash
pip install pytest pytest-cov pytest-mock pytest-asyncio httpx
```

### Estructura de Archivos

```
backend-acorag/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Fixtures compartidas
│   ├── test_ingest.py           # Tests de ingesta
│   ├── test_embeddings.py       # Tests de embeddings
│   ├── test_search.py           # Tests de búsqueda
│   ├── test_chat.py             # Tests de chat/RAG
│   ├── test_upload.py           # Tests de upload
│   ├── test_auth.py             # Tests de autenticación
│   └── test_utils.py            # Tests de utilidades
├── pytest.ini                   # Configuración de pytest
└── .coveragerc                  # Configuración de cobertura
```

---

## ▶️ Comandos de Ejecución

### Ejecutar todos los tests
```bash
pytest tests/ -v
```

### Ejecutar tests con cobertura
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

### Ejecutar un test específico
```bash
pytest tests/test_ingest.py::test_normalize_doc_complete -v
```

### Ejecutar tests en paralelo (más rápido)
```bash
pytest tests/ -n auto
```

### Ejecutar solo tests marcados
```bash
pytest tests/ -m "unit"      # Solo tests unitarios
pytest tests/ -m "integration"  # Solo tests de integración
```

---

## 📊 Cobertura Esperada

| Módulo | Cobertura Objetivo | Prioridad |
|--------|-------------------|-----------|
| `app/ingest.py` | >= 85% | 🔴 Alta |
| `app/search_core.py` | >= 90% | 🔴 Alta |
| `app/upload.py` | >= 80% | 🟡 Media |
| `app/utils.py` | >= 95% | 🟢 Baja |
| `app/auth.py` | >= 85% | 🟡 Media |
| `app/api.py` | >= 75% | 🟡 Media |

**Meta general:** >= 80% de cobertura en todo el proyecto

---

## 🎨 Mejores Prácticas

### 1. Uso de Fixtures

```python
@pytest.fixture
def mock_db():
    """Mock de conexión a base de datos"""
    return MagicMock()

@pytest.fixture
def sample_document():
    """Documento de prueba reutilizable"""
    return {
        "DocumentId": "DOC-001",
        "metadata": {
            "Title": "Test Document",
            "DocumentNumber": "TD-001"
        }
    }
```

### 2. Mocking de Dependencias Externas

```python
@patch('app.ingest.SentenceTransformer')
def test_with_mock_model(mock_transformer):
    mock_model = mock_transformer.return_value
    mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
    # ... test code
```

### 3. Tests Parametrizados

```python
@pytest.mark.parametrize("query,expected_count", [
    ("plano arquitectura", 10),
    ("cronograma obra", 5),
    ("presupuesto", 15),
])
def test_search_various_queries(query, expected_count):
    results = semantic_search(query, None, top_k=20)
    assert len(results) >= expected_count
```

### 4. Tests Asíncronos para API

```python
@pytest.mark.asyncio
async def test_upload_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/upload", files={"file": content})
    assert response.status_code == 200
```

---

## 🚨 Casos Edge Críticos

### 1. Manejo de Errores
- ❌ Base de datos no disponible
- ❌ Modelo de embeddings falla al cargar
- ❌ Query malformado
- ❌ Token JWT expirado

### 2. Límites del Sistema
- 📏 Documento muy grande (> 200KB)
- 📏 Muchos chunks (> 1000)
- 📏 Query muy largo (> 5000 chars)
- 📏 Batch muy grande (> 1000 docs)

### 3. Datos Inválidos
- 🚫 JSON malformado
- 🚫 Fecha en formato incorrecto
- 🚫 Metadatos faltantes
- 🚫 Encoding incorrecto

---

## 📈 Métricas de Calidad

### Tests Deben Ser:
1. **FAST**: < 5 segundos por test (unitarios)
2. **INDEPENDENT**: No dependen de otros tests
3. **REPEATABLE**: Mismo resultado siempre
4. **SELF-VALIDATING**: Pass o fail claro
5. **TIMELY**: Escritos junto con el código

### Criterios de Éxito:
- ✅ Todos los tests pasan
- ✅ Cobertura >= 80%
- ✅ 0 warnings críticos
- ✅ Tiempo total < 2 minutos
- ✅ Tests documentados y legibles

---

## 🔄 CI/CD Integration

### GitHub Actions (ejemplo)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest tests/ --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 📚 Referencias

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Última actualización:** 2025-11-24  
**Versión:** 1.0  
**Autor:** GitHub Copilot
