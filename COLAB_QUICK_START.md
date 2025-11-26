# 🚀 Ejecutar Tests en Google Colab - Guía Rápida

## 3 Formas de Hacerlo (NO necesitas GitHub)

### ⭐ **OPCIÓN 1: Subir ZIP (MÁS FÁCIL - RECOMENDADO)**

#### Pasos:
1. **Crear el ZIP** (elige una):
   - **Automático**: Ejecuta `.\crear_zip_para_colab.ps1` en PowerShell
   - **Manual**: Comprime la carpeta `backend-acorag` en un ZIP

2. **Subir notebook a Drive**:
   - Sube `tests_colab.ipynb` a tu Google Drive
   - Abre con Google Colaboratory

3. **Ejecutar**:
   - En el **Paso 1**, ejecuta la celda
   - Sube el archivo ZIP cuando te lo pida
   - Ejecuta el resto del notebook

✅ **No necesitas**: Git, GitHub, repo público, configuración

---

### 📁 **OPCIÓN 2: Google Drive**

#### Pasos:
1. **Subir archivos**:
   - Copia toda la carpeta `backend-acorag` a tu Google Drive
   - Sube también `tests_colab.ipynb`

2. **Configurar ruta**:
   - Abre el notebook en Colab
   - En **Paso 1**, descomenta la **OPCIÓN C**
   - Cambia la ruta: `/content/drive/MyDrive/TU_RUTA/backend-acorag`

3. **Ejecutar**:
   - Runtime → Run all
   - Autoriza acceso a Drive

✅ **Ventaja**: Puedes editar archivos en Drive y re-ejecutar tests

---

### 🌐 **OPCIÓN 3: GitHub (Solo si el repo es público)**

#### Pasos:
1. **Hacer repo público** (si no lo es):
   - GitHub → Settings → Danger Zone → Make public

2. **Abrir notebook**:
   - Visita: https://colab.research.google.com/
   - Pestaña "GitHub" → Pega tu URL del repo
   - Abre `backend-acorag/tests_colab.ipynb`

3. **Ejecutar**:
   - En **Paso 1**, descomenta la **OPCIÓN A**
   - Runtime → Run all

✅ **Ventaja**: Link compartible directo con tu asesor

---

## 📊 ¿Qué Incluir en el ZIP?

El script `crear_zip_para_colab.ps1` incluye automáticamente:

```
backend-acorag/
├── app/                          # Código fuente
│   ├── ingest.py
│   ├── search_core.py
│   ├── upload.py
│   └── utils.py
├── tests/                        # Tests (19 tests)
│   ├── conftest.py
│   ├── test_ingest.py
│   ├── test_search.py
│   ├── test_upload.py
│   └── test_utils.py
├── requirements.txt              # Dependencias
├── DOCUMENTACION_TESTS.md        # Docs completa
├── ERRORES_Y_SOLUCIONES_TESTS.md
├── TESTING_SUMMARY.md
└── README.md
```

**Tamaño aproximado**: 500 KB - 2 MB

---

## 🎯 Para tu Asesor

### Link Directo (si usas Opción 3 - GitHub):
```
https://colab.research.google.com/github/luiscornejo1/back-acorag/blob/main/backend-acorag/tests_colab.ipynb
```

### Instrucciones Simplificadas:
1. Abre el link de arriba (o el notebook que le compartas)
2. En el **Paso 1**, elige cómo cargar los archivos (ZIP, Drive, o GitHub)
3. Ejecuta: Runtime → Run all
4. Espera 3-5 minutos
5. Verás resultados al final: **19/19 tests pasando (100%)**

---

## 🔧 Troubleshooting

### Error: "No such file or directory: 'tests/'"
**Causa**: No se cargaron correctamente los archivos  
**Solución**: 
- Verifica que el ZIP contenga la estructura correcta
- Revisa que estés en el directorio correcto: `%cd backend-acorag`

### Error: "ModuleNotFoundError: No module named 'app'"
**Causa**: Falta el directorio `app/` con el código fuente  
**Solución**: 
- Asegúrate de incluir la carpeta `app/` en el ZIP
- Ejecuta el script `crear_zip_para_colab.ps1` para crear el ZIP correcto

### Error al subir ZIP: "File too large"
**Causa**: El ZIP es muy grande (>100 MB)  
**Solución**: 
- Elimina archivos innecesarios: `__pycache__`, `.venv`, `data/`, etc.
- El ZIP solo debe tener ~500 KB - 2 MB

---

## 📝 Archivos Necesarios

### Mínimo para ejecutar tests:
- ✅ `tests_colab.ipynb` (el notebook)
- ✅ `backend-acorag/` (carpeta completa o ZIP)

### Archivos opcionales (documentación):
- 📄 `COLAB_INSTRUCTIONS.md` (instrucciones detalladas)
- 📄 `DOCUMENTACION_TESTS.md` (dentro del ZIP)

---

## 🎉 Resultado Esperado

Al final del notebook verás:

```
================================================================================
📊 RESUMEN FINAL DE TESTS
================================================================================

✅ Tests Pasando: 19/19 (100.0%)
❌ Tests Fallando: 0/19 (0.0%)

📁 Archivos Testeados:
   - app/ingest.py
   - app/search_core.py
   - app/upload.py
   - app/utils.py

🎯 Objetivo: 19/19 tests pasando (100%)
📈 Estado Actual: 19/19 (100.0%)

🎉 ¡TODOS LOS TESTS PASANDO! Sistema RAG validado correctamente.
```

---

**Fecha**: Noviembre 25, 2025  
**Versión**: 1.0  
**Mantenedor**: Luis Cornejo
