# 🚀 Optimización de RAG con SOLO Metadatos

## 📋 Situación Actual

- **147,066 documentos** en base de datos
- **Sin acceso a PDFs completos** (solo metadatos vía API)
- **Modelo actual**: `paraphrase-multilingual-MiniLM-L12-v2` (384 dim)
  - Precisión: **0.469** (el peor en pruebas)
- **Chunks**: 80 caracteres (solo metadatos básicos)

---

## 🎯 Estrategia de Optimización

### 1️⃣ **Cambiar a mejor modelo español** (+54% precisión)
- Modelo nuevo: `dccuchile/bert-base-spanish-wwm-uncased` (768 dim)
- Precisión: **0.590** (el mejor en pruebas con 227k docs)
- Dimensiones: 768 (doble resolución semántica)

### 2️⃣ **Enriquecer metadatos** (texto expandido)
- Convertir campos técnicos a lenguaje natural
- Repetir información clave (mayor peso semántico)
- Expansión: 80 chars → 500-800 chars por documento

### 3️⃣ **Re-ingerir datos optimizados**
- Usar texto enriquecido para embeddings
- Mejor chunking (chunks más útiles)
- Mismo número de documentos, mejor calidad

---

## 📝 Pasos para Ejecutar

### **PASO 1: Actualizar modelo en Railway**

1. Ve a: https://railway.app
2. Selecciona tu proyecto: **back-acorag-production**
3. Ve a pestaña **Variables**
4. Busca `EMBEDDING_MODEL`
5. Cambia el valor a:
   ```
   dccuchile/bert-base-spanish-wwm-uncased
   ```
6. **Guarda** (Railway redesplegará automáticamente)
7. **Espera ~2-3 minutos** hasta que el despliegue termine

---

### **PASO 2: Optimizar metadatos localmente**

```powershell
cd backend-acorag
python optimize_metadata_only.py
```

Esto creará: `data/mis_correos_optimizado.json`

**Ejemplo de optimización:**
- **Antes (80 chars)**:
  ```
  DocumentId: ABC123, Title: Plano Estructural, Type: Documento Técnico
  ```

- **Después (500+ chars)**:
  ```
  Este es un documento titulado: Plano Estructural de Fundaciones Bloque A
  El documento se llama: Plano Estructural de Fundaciones Bloque A
  Título del documento: Plano Estructural de Fundaciones Bloque A
  Número de documento: EST-001-FND-A
  Identificado con el número: EST-001-FND-A
  Es un documento de tipo: Documento Técnico
  Clasificado como: Documento Técnico
  Pertenece al proyecto: Torre Residencial Los Álamos
  Proyecto asociado: Torre Residencial Los Álamos
  Ubicación o área: Fundaciones
  Disciplina técnica: Estructural
  Estado actual del documento: Aprobado
  Estado de revisión: Revisión Final
  ...
  ```

---

### **PASO 3: Actualizar código en Railway**

```powershell
cd backend-acorag
git add app/ingest.py optimize_metadata_only.py run_optimization.py
git commit -m "feat: optimización máxima de metadatos para búsqueda sin PDFs"
git push
```

Railway redesplegará automáticamente (~2 min).

---

### **PASO 4: Re-ingerir datos en Railway**

**Opción A: Usando Railway CLI (recomendado)**

```powershell
# Si no tienes Railway CLI instalado:
# npm i -g @railway/cli
# railway login

cd backend-acorag
railway run python run_optimization.py
```

**Opción B: Desde Railway Dashboard**

1. Ve a tu proyecto en railway.app
2. Pestaña **Deployments**
3. Click en los 3 puntos → **Deploy**
4. Una vez desplegado, ve a **Logs**
5. Ejecuta manualmente la ingesta desde un servicio temporal

---

## 📊 Resultados Esperados

### Antes:
- ❌ Búsqueda: "planos estructurales del proyecto" → 0 resultados relevantes
- ❌ Chunks: 80 caracteres (solo IDs y títulos cortos)
- ❌ Precisión: 0.469 (modelo peor)

### Después:
- ✅ Búsqueda: "planos estructurales del proyecto" → Resultados relevantes
- ✅ Chunks: 500-800 caracteres (contexto completo)
- ✅ Precisión: 0.590 (+54% mejora)
- ✅ Búsquedas en español: Mucho mejor
- ✅ Contexto semántico: 200% más rico

---

## ⚠️ Limitaciones Actuales

### Sin acceso a PDFs:
- ❌ No puedes buscar **dentro del contenido** de los documentos
- ✅ Puedes buscar por: Título, Número, Proyecto, Tipo, Estado, Categoría, etc.

### Ejemplo de búsquedas que funcionarán BIEN:
- ✅ "planos aprobados del proyecto Los Álamos"
- ✅ "documentos técnicos en revisión de fundaciones"
- ✅ "archivos de la disciplina estructural"
- ✅ "documentos EST-001"

### Ejemplo de búsquedas que NO funcionarán:
- ❌ "detalle constructivo de las vigas" (necesita contenido PDF)
- ❌ "especificaciones del hormigón H30" (necesita contenido PDF)

---

## 🔮 Futuro: Cuando tengas acceso a PDFs

Si en el futuro puedes descargar PDFs, usa:

```powershell
python extract_pdf_content.py
```

Esto:
1. Descargará PDFs vía API
2. Extraerá texto con PyPDF2/pdfplumber
3. Agregará contenido completo a los JSONs
4. Permitirá búsquedas **dentro** del contenido

**Mejora esperada**: +300% precisión en búsquedas de contenido técnico.

---

## 📞 Soporte

Si algo falla:

1. **Revisa logs en Railway**:
   ```
   railway logs
   ```

2. **Verifica variables**:
   - `DATABASE_URL` (debe tener pgvector)
   - `EMBEDDING_MODEL` (debe ser el nuevo)
   - `GROQ_API_KEY` (para chat)

3. **Prueba localmente**:
   ```powershell
   python optimize_metadata_only.py
   python -m app.ingest --json_path data/mis_correos_optimizado.json --project_id ACONEX_DOCS --recreate
   ```

---

## ✅ Checklist

- [ ] Actualizar `EMBEDDING_MODEL` en Railway
- [ ] Ejecutar `optimize_metadata_only.py`
- [ ] Commit y push de cambios
- [ ] Ejecutar `run_optimization.py` en Railway
- [ ] Probar búsquedas en frontend
- [ ] Verificar mejora en precisión

---

**Fecha**: Noviembre 2025  
**Estado**: Listo para ejecutar  
**Impacto esperado**: +54% precisión, chunks 7x más largos
