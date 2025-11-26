# 🚀 Instrucciones para Ejecutar Tests en Google Colab

## 📋 Pasos para tu Asesor

### **Opción 1: Subir Archivos ZIP (MÁS FÁCIL - Recomendado) ⭐**

1. **Preparar archivos localmente**
   - Comprime tu carpeta `backend-acorag` en un archivo ZIP
   - Incluye todos los archivos: `app/`, `tests/`, archivos `.md`, etc.

2. **Subir el notebook a Google Drive**
   - Descarga el archivo `tests_colab.ipynb` de este repositorio
   - Súbelo a tu Google Drive

3. **Abrir en Google Colab**
   - Haz clic derecho en el archivo → "Abrir con" → "Google Colaboratory"
   - Si no aparece Colab, instálalo desde Google Workspace Marketplace

4. **Ejecutar el Notebook**
   - En el **Paso 1**, ejecuta la celda (no toques las líneas comentadas)
   - Te pedirá subir un archivo → selecciona tu `backend-acorag.zip`
   - Continúa ejecutando las demás celdas en orden (Shift + Enter)
   - O ejecuta todo: "Runtime" → "Run all"

5. **Resultados**
   - Verás el output de cada test en tiempo real
   - Al final aparecerá un resumen con estadísticas completas

**Ventajas:**
- ✅ No necesitas repositorio público en GitHub
- ✅ No necesitas configurar Git
- ✅ Funciona completamente offline (solo necesitas internet para Colab)

---

### **Opción 2: Usar Google Drive**

1. **Subir archivos a Google Drive**
   - Crea una carpeta en tu Google Drive (ej: `Mis Proyectos/backend-acorag`)
   - Sube TODA la carpeta `backend-acorag` con su contenido

2. **Abrir el notebook en Colab**
   - Sube `tests_colab.ipynb` a tu Google Drive
   - Ábrelo con Google Colaboratory

3. **Configurar la ruta en el notebook**
   - En el **Paso 1**, comenta las otras opciones
   - Descomenta la **OPCIÓN C** (Google Drive)
   - Cambia la ruta: `/content/drive/MyDrive/backend-acorag` por tu ruta real
   - Ejemplo: `/content/drive/MyDrive/Mis Proyectos/backend-acorag`

4. **Ejecutar**
   - Runtime → Run all
   - Autoriza el acceso a Google Drive cuando te lo pida
   - Los tests se ejecutarán automáticamente

**Ventajas:**
- ✅ No necesitas comprimir archivos
- ✅ Puedes editar archivos directamente en Drive y re-ejecutar tests
- ✅ Los cambios persisten entre sesiones

---

### **Opción 3: Clonar desde GitHub (Solo si el repo es público)**

### **Opción 3: Clonar desde GitHub (Solo si el repo es público)**

1. **Hacer el repositorio público (si no lo es)**
   - Ve a GitHub → Configuración del repositorio → Danger Zone
   - Change repository visibility → Make public

2. **Abrir directamente desde GitHub**
   - Visita: https://colab.research.google.com/
   - En la pestaña "GitHub", pega la URL del repositorio:
     ```
     https://github.com/luiscornejo1/back-acorag
     ```
   - Selecciona el archivo `backend-acorag/tests_colab.ipynb`

3. **Ejecutar**
   - En el **Paso 1**, descomenta la **OPCIÓN A** (GitHub)
   - Runtime → Run all
   - Espera ~2-3 minutos para instalación de dependencias
   - Los tests se ejecutarán automáticamente

**Ventajas:**
- ✅ Link directo compartible con tu asesor
- ✅ Siempre usa la última versión del código
- ✅ No necesitas subir archivos manualmente

**Desventajas:**
- ❌ Requiere que el repo sea público

---

### **Opción 4: Crear Notebook Manualmente (Para Expertos)**

Si prefieres crearlo desde cero en Colab:

#### **Celda 1: Clonar Repositorio**
```python
!git clone https://github.com/luiscornejo1/back-acorag.git
%cd back-acorag/backend-acorag
```

#### **Celda 2: Instalar Dependencias**
```python
!pip install -q pytest pytest-asyncio pytest-mock
!pip install -q psycopg2-binary numpy sentence-transformers
!pip install -q pyjwt python-jose[cryptography] bcrypt passlib
```

#### **Celda 3: Ejecutar Tests**
```python
!pytest tests/ -v --tb=short --color=yes
```

#### **Celda 4: Ver Resumen**
```python
import subprocess
result = subprocess.run(['pytest', 'tests/', '-v'], capture_output=True, text=True)
output = result.stdout + result.stderr

# Contar resultados
import re
passed = len(re.findall(r'PASSED', output))
failed = len(re.findall(r'FAILED', output))
total = passed + failed

print(f"✅ Tests Pasando: {passed}/{total} ({passed/total*100:.1f}%)")
print(f"❌ Tests Fallando: {failed}/{total}")
print(f"\n🎯 Objetivo: 19/19 tests (100%)")
```

---

## 📊 Qué Esperar

### **Output Esperado**

```
==================== test session starts ====================
collected 19 items

tests/test_ingest.py::test_normalize_doc_complete PASSED                    [  5%]
tests/test_ingest.py::test_iter_docs_from_file_json_and_ndjson PASSED      [ 10%]
tests/test_ingest.py::test_normalize_doc_missing_fields PASSED             [ 15%]
tests/test_ingest.py::test_iter_docs_invalid_json PASSED                   [ 21%]

tests/test_search.py::test_semantic_search_basic PASSED                    [ 26%]
tests/test_search.py::test_semantic_search_with_project_filter PASSED      [ 31%]
tests/test_search.py::test_semantic_search_empty_query PASSED              [ 36%]
tests/test_search.py::test_semantic_search_invalid_project_id PASSED       [ 42%]

tests/test_upload.py::test_extract_text_from_txt PASSED                    [ 47%]
tests/test_upload.py::test_generate_document_id_unique PASSED              [ 52%]
tests/test_upload.py::test_extract_text_file_not_found PASSED              [ 57%]
tests/test_upload.py::test_extract_text_invalid_encoding PASSED            [ 63%]

tests/test_utils.py::test_simple_chunk_with_overlap PASSED                 [ 68%]
tests/test_utils.py::test_get_db_connection_success PASSED                 [ 73%]
tests/test_utils.py::test_simple_chunk_edge_cases PASSED                   [ 78%]
tests/test_utils.py::test_simple_chunk_invalid_parameters PASSED           [ 84%]
tests/test_utils.py::test_get_db_connection_invalid_credentials PASSED     [ 89%]
tests/test_utils.py::test_get_db_connection_missing_env_vars PASSED        [ 94%]

==================== 19 passed in 5.23s ====================
```

### **Resumen Final**

```
📊 RESUMEN FINAL DE TESTS
================================================================================
✅ Tests Pasando: 19/19 (100.0%)
❌ Tests Fallando: 0/19 (0.0%)

📁 Archivos Testeados:
   - app/ingest.py (normalización y lectura de documentos)
   - app/search_core.py (búsqueda semántica vectorial)
   - app/upload.py (procesamiento de archivos)
   - app/utils.py (chunking y conexión BD)

🎯 Objetivo: 19/19 tests pasando (100%)
📈 Estado Actual: 19/19 (100.0%)

🎉 ¡TODOS LOS TESTS PASANDO! Sistema RAG validado correctamente.
```

---

## 🔧 Troubleshooting

### **Problema 1: Error al clonar repositorio**
```
fatal: could not read Username for 'https://github.com'
```

**Solución**: El repositorio debe ser público. Verifica en GitHub que el repo esté en modo público.

---

### **Problema 2: Módulo no encontrado**
```
ModuleNotFoundError: No module named 'app'
```

**Solución**: Asegúrate de estar en el directorio correcto:
```python
%cd back-acorag/backend-acorag
!pwd  # Verificar directorio actual
```

---

### **Problema 3: Tests fallan por dependencias**
```
ImportError: cannot import name 'get_db_connection'
```

**Solución**: Instala todas las dependencias nuevamente:
```python
!pip install --upgrade -r requirements.txt
```

---

## 📖 Documentación Adicional

Dentro del notebook, tu asesor puede ver:

1. **DOCUMENTACION_TESTS.md** - Documentación completa de todos los tests
   ```python
   !cat DOCUMENTACION_TESTS.md
   ```

2. **ERRORES_Y_SOLUCIONES_TESTS.md** - Troubleshooting detallado
   ```python
   !cat ERRORES_Y_SOLUCIONES_TESTS.md
   ```

3. **TESTING_SUMMARY.md** - Resumen ejecutivo
   ```python
   !cat TESTING_SUMMARY.md
   ```

---

## 🎯 Tests Incluidos

### **Tests Positivos (9)** - Validación de funcionalidad correcta
- ✅ Normalización completa de documentos Aconex
- ✅ Lectura de archivos JSON/NDJSON
- ✅ Búsqueda semántica vectorial básica
- ✅ Filtrado por proyecto (multi-tenancy)
- ✅ Extracción de texto de archivos TXT
- ✅ Generación única de IDs (MD5)
- ✅ Chunking de texto con overlap
- ✅ Conexión a base de datos PostgreSQL
- ✅ Casos extremos de chunking

### **Tests Negativos (10)** - Validación de manejo de errores
- 🚨 Documentos con campos faltantes
- 🚨 Archivos JSON malformados
- 🚨 Queries de búsqueda vacías
- 🚨 Proyectos inexistentes
- 🚨 Archivos no encontrados (FileNotFoundError)
- 🚨 Archivos con encoding corrupto
- 🚨 Parámetros inválidos (size=0, overlap>size)
- 🚨 Credenciales de BD incorrectas
- 🚨 Variables de entorno faltantes

---

## 📧 Contacto

Si tu asesor tiene dudas:
- **Repositorio**: https://github.com/luiscornejo1/back-acorag
- **Documentación**: Ver archivos `DOCUMENTACION_TESTS.md` y `TESTING_SUMMARY.md`
- **Issues**: Crear issue en GitHub para preguntas específicas

---

**Última actualización**: Noviembre 25, 2025  
**Versión del Notebook**: 1.0
