# 🧪 Guía de Ejecución de Tests - Aconex RAG

## ✅ Estado Actual: 9/9 Tests Pasando (100%)

**Última actualización**: Suite de tests simplificada y enfocada en la funcionalidad core del sistema RAG, con **100% de éxito** en tests unitarios.

### 📊 Estadísticas de Tests

| Módulo | Tests | Estado | Cobertura |
|--------|-------|--------|-----------|
| `test_ingest.py` | 2 | ✅ 2/2 | Normalización, parsing |
| `test_search.py` | 2 | ✅ 2/2 | Búsqueda, filtrado |
| `test_upload.py` | 2 | ✅ 2/2 | Extracción, IDs |
| `test_utils.py` | 3 | ✅ 3/3 | Chunking, conexión |
| **TOTAL** | **9** | **✅ 9/9 (100%)** | **Core funcionalidad** |

### 🎯 Escenarios Cubiertos

1. **Ingesta de Documentos**: Normalización Aconex, parsing JSON/NDJSON
2. **Búsqueda Semántica**: Vector search, multi-tenancy, ranking híbrido
3. **Upload en Tiempo Real**: Extracción TXT, generación de IDs determinísticos
4. **Utilidades Core**: Chunking con overlap, conexión BD, casos borde

---

Esta guía te ayudará a instalar las dependencias de testing y ejecutar todos los tests del sistema.

---

## 📦 Instalación de Dependencias

### 1. Activar el entorno virtual

```powershell
& .\.venv311\Scripts\Activate.ps1
```

### 2. Instalar dependencias de testing

```powershell
pip install pytest pytest-cov pytest-mock pytest-asyncio httpx pytest-xdist
```

O si tienes un archivo `requirements-test.txt`:

```powershell
pip install -r requirements-test.txt
```

---

## ▶️ Comandos de Ejecución

### Tests Básicos

#### Ejecutar todos los tests
```powershell
pytest tests/ -v
```

#### Ejecutar tests con salida detallada
```powershell
pytest tests/ -vv --tb=long
```

#### Ejecutar tests con progreso en tiempo real
```powershell
pytest tests/ -v --tb=short
```

---

### Tests con Cobertura

#### Cobertura básica (terminal)
```powershell
pytest tests/ --cov=app --cov-report=term
```

#### Cobertura con porcentajes y líneas faltantes
```powershell
pytest tests/ --cov=app --cov-report=term-missing
```

#### Generar reporte HTML (recomendado)
```powershell
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

Luego abrir: `htmlcov/index.html` en el navegador

#### Cobertura completa con XML (para CI/CD)
```powershell
pytest tests/ --cov=app --cov-report=xml --cov-report=html --cov-report=term
```

---

### Tests Específicos

#### Ejecutar un archivo de test específico
```powershell
pytest tests/test_ingest.py -v
```

#### Ejecutar una función de test específica
```powershell
pytest tests/test_ingest.py::test_normalize_doc_complete -v
```

#### Ejecutar tests de un módulo específico
```powershell
pytest tests/test_search.py -v
```

#### Ejecutar múltiples archivos
```powershell
pytest tests/test_ingest.py tests/test_search.py -v
```

---

### Tests por Markers (Categorías)

#### Solo tests unitarios
```powershell
pytest tests/ -m "unit" -v
```

#### Solo tests de integración
```powershell
pytest tests/ -m "integration" -v
```

#### Solo tests de API
```powershell
pytest tests/ -m "api" -v
```

#### Solo tests que usan mocks
```powershell
pytest tests/ -m "mock" -v
```

#### Solo tests de base de datos
```powershell
pytest tests/ -m "db" -v
```

#### Excluir tests lentos
```powershell
pytest tests/ -m "not slow" -v
```

---

### Tests en Paralelo (Más Rápido)

#### Ejecutar en todos los cores disponibles
```powershell
pytest tests/ -n auto
```

#### Ejecutar en 4 procesos paralelos
```powershell
pytest tests/ -n 4
```

#### Paralelo + cobertura
```powershell
pytest tests/ -n auto --cov=app --cov-report=html
```

---

### Tests con Filtros

#### Tests que contengan "search" en el nombre
```powershell
pytest tests/ -k "search" -v
```

#### Tests que NO contengan "slow"
```powershell
pytest tests/ -k "not slow" -v
```

#### Tests de búsqueda o ingesta
```powershell
pytest tests/ -k "search or ingest" -v
```

---

### Debugging

#### Modo verbose con traceback completo
```powershell
pytest tests/test_ingest.py -vv --tb=long
```

#### Mostrar prints durante ejecución
```powershell
pytest tests/ -v -s
```

#### Parar en el primer error
```powershell
pytest tests/ -x
```

#### Parar después de N errores
```powershell
pytest tests/ --maxfail=3
```

#### Ejecutar solo tests que fallaron la última vez
```powershell
pytest tests/ --lf
```

#### Ejecutar primero los que fallaron, luego los demás
```powershell
pytest tests/ --ff
```

---

### Generación de Reportes

#### Reporte JUnit XML (para CI/CD)
```powershell
pytest tests/ --junit-xml=test-results.xml
```

#### Reporte en formato JSON
```powershell
pytest tests/ --json-report --json-report-file=test-report.json
```

---

## 📊 Análisis de Cobertura

### Ver líneas no cubiertas por tests

```powershell
pytest tests/ --cov=app --cov-report=term-missing
```

### Generar reporte anotado

```powershell
pytest tests/ --cov=app --cov-report=annotate
```

Esto crea archivos `.py,cover` con anotaciones de cobertura.

### Ver cobertura por módulo

```powershell
pytest tests/ --cov=app --cov-report=term --cov-config=.coveragerc
```

---

## 🎯 Escenarios Comunes

### Desarrollo: Ejecutar tests rápidamente
```powershell
pytest tests/ -v --tb=short -x
```

### Pre-commit: Verificar todo antes de commit
```powershell
pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80
```

### CI/CD: Reporte completo
```powershell
pytest tests/ -v --cov=app --cov-report=xml --cov-report=html --junit-xml=test-results.xml
```

### Debugging de un test específico
```powershell
pytest tests/test_search.py::test_semantic_search_basic -vv -s --tb=long
```

### Ver qué tests se ejecutarán (sin ejecutarlos)
```powershell
pytest tests/ --collect-only
```

---

## 🐛 Troubleshooting

### Error: "No module named 'app'"

```powershell
# Asegúrate de estar en el directorio backend-acorag
cd backend-acorag
pytest tests/ -v
```

### Error: "DATABASE_URL not set"

Los tests usan variables de entorno mock. Si ves este error, verifica que `conftest.py` esté configurando correctamente las variables en la fixture `test_env_vars`.

### Error: ImportError para PyPDF2 o python-docx

```powershell
pip install PyPDF2 python-docx
```

### Tests muy lentos

```powershell
# Ejecutar en paralelo
pytest tests/ -n auto

# O excluir tests lentos
pytest tests/ -m "not slow"
```

### Ver warnings detallados

```powershell
pytest tests/ -v -W all
```

---

## 📈 Métricas de Calidad

### Verificar que la cobertura sea >= 80%

```powershell
pytest tests/ --cov=app --cov-fail-under=80
```

### Contar número de tests

```powershell
pytest tests/ --collect-only -q
```

### Ver estadísticas de tests

```powershell
pytest tests/ -v --durations=10
```

Esto muestra los 10 tests más lentos.

---

## 🔄 Integración Continua

### GitHub Actions

Ejemplo de workflow (`.github/workflows/tests.yml`):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-mock pytest-asyncio httpx
      
      - name: Run tests
        run: |
          cd backend-acorag
          pytest tests/ --cov=app --cov-report=xml --cov-report=html --junit-xml=test-results.xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend-acorag/coverage.xml
```

---

## 📝 Tips y Mejores Prácticas

### 1. Ejecutar tests frecuentemente

Durante desarrollo, ejecuta:
```powershell
pytest tests/ -x -v
```

Esto para en el primer error y te ahorra tiempo.

### 2. Usar markers para organizar

```powershell
# Solo tests rápidos durante desarrollo
pytest tests/ -m "unit and not slow"

# Tests de integración antes de push
pytest tests/ -m "integration"
```

### 3. Ver cobertura de un módulo específico

```powershell
pytest tests/test_ingest.py --cov=app.ingest --cov-report=term-missing
```

### 4. Cachear resultados

```powershell
# Pytest cachea resultados automáticamente
# Para limpiar el cache:
pytest --cache-clear
```

### 5. Generar reporte de performance

```powershell
pytest tests/ -v --durations=0
```

Muestra duración de TODOS los tests.

---

## 🎓 Recursos Adicionales

- [Documentación de pytest](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Testing FastAPI](https://fastapi.tiangolo.com/tutorial/testing/)
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - Estrategia completa de testing

---

## ✅ Checklist Pre-Commit

Antes de hacer commit, ejecuta:

- [ ] `pytest tests/ -v` - Todos los tests pasan
- [ ] `pytest tests/ --cov=app --cov-report=term` - Cobertura >= 80%
- [ ] `pytest tests/ -m "integration"` - Tests de integración OK
- [ ] Revisar el reporte HTML de cobertura

---

**Última actualización:** 2025-11-24  
**Versión:** 1.0
