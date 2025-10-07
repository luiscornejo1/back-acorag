# 🚀 Guía de Despliegue en Railway

## ✅ Optimizaciones Aplicadas

### 1. **IVFFlat Index Optimization**
- **Antes**: `lists = 100`
- **Ahora**: `lists = 470`
- **Razón**: Fórmula óptima `sqrt(221,306 chunks) = 470` para mejor rendimiento de búsqueda vectorial

### 2. **Chunk Size Optimization**
- **Antes**: `size = 1200` caracteres
- **Ahora**: `size = 2400` caracteres
- **Razón**: Mejor preservación del contexto de correos electrónicos completos

### 3. **Overlap Optimization**
- **Antes**: `overlap = 200` caracteres
- **Ahora**: `overlap = 240` caracteres (10% del chunk size)
- **Razón**: Proporción óptima para evitar pérdida de contexto entre chunks

---

## 📋 Pre-requisitos

1. **Cuenta de Railway**: [Registrarse en Railway](https://railway.app/)
2. **Repositorio GitHub**: Tu código ya está en `luiscornejo1/back-acorag`
3. **PostgreSQL con pgvector**: Railway lo provee automáticamente

---

## 🛠️ Paso 1: Crear Proyecto en Railway

1. Ve a [Railway Dashboard](https://railway.app/dashboard)
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Autoriza Railway para acceder a tu repositorio
5. Selecciona el repositorio `luiscornejo1/back-acorag`

---

## 🗄️ Paso 2: Agregar PostgreSQL con pgvector

1. En tu proyecto de Railway, click en **"+ New"**
2. Selecciona **"Database" → "Add PostgreSQL"**
3. Railway creará automáticamente una base de datos PostgreSQL
4. **Instalar pgvector**:
   - Ve a la pestaña **"Settings"** de tu base de datos PostgreSQL
   - En **"Connect"**, copia la **"Postgres Connection URL"**
   - Usa un cliente PostgreSQL (DBeaver, pgAdmin, o `psql`) para conectarte
   - Ejecuta este comando SQL:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```

---

## ⚙️ Paso 3: Configurar Variables de Entorno

En la configuración de tu servicio backend de Railway, agrega estas variables de entorno:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `DATABASE_URL` | *Auto-generada por Railway* | Railway la conecta automáticamente si agregaste PostgreSQL |
| `EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Modelo de embeddings |
| `OPENAI_API_KEY` | `tu-api-key-de-openai` | Clave API de OpenAI (si usas GPT) |
| `OPENAI_MODEL` | `gpt-4o` | Modelo de OpenAI a usar |
| `PORT` | *Auto-generada por Railway* | Railway la asigna automáticamente |

### Cómo agregar variables:
1. Click en tu servicio backend
2. Ve a **"Variables"**
3. Click en **"+ New Variable"**
4. Agrega cada variable con su valor

---

## 📦 Paso 4: Desplegar

Railway detectará automáticamente tu `Procfile` y `railway.json` y desplegará tu aplicación.

### Archivos de configuración creados:
- ✅ `Procfile`: Define el comando de inicio
- ✅ `railway.json`: Configuración específica de Railway
- ✅ `runtime.txt`: Especifica Python 3.11
- ✅ `requirements.txt`: Dependencias actualizadas

### Proceso de despliegue:
1. Railway detecta el push a GitHub
2. Instala dependencias de `requirements.txt`
3. Ejecuta el comando del `Procfile`: `uvicorn app.server:app --host 0.0.0.0 --port $PORT`
4. Tu API estará disponible en `https://tu-proyecto.railway.app`

---

## 🔄 Paso 5: Reindexar Base de Datos (Crítico)

⚠️ **IMPORTANTE**: Las optimizaciones de IVFFlat y chunking requieren reindexar tu base de datos.

### Opción 1: Desde Railway (Recomendado)
1. Sube tu archivo `mis_correos.json` a un servicio de almacenamiento (Google Drive, S3, etc.)
2. Desde la terminal de Railway, ejecuta:
   ```bash
   python -m app.ingest path/to/mis_correos.json proyecto_id
   ```

### Opción 2: Desde Local
1. Actualiza `DATABASE_URL` en tu `.env` local con la URL de Railway
2. Ejecuta localmente:
   ```bash
   python -m app.ingest data/mis_correos.json proyecto_id
   ```

### ¿Por qué reindexar?
- El índice IVFFlat con `lists=470` solo se crea durante `ensure_schema()`
- Los chunks con `size=2400, overlap=240` solo se generan durante la ingesta
- Los datos existentes con configuración antigua quedarán obsoletos

---

## 🧪 Paso 6: Verificar Despliegue

### 1. Health Check
```bash
curl https://tu-proyecto.railway.app/health
```
**Respuesta esperada**: `{"ok": true}`

### 2. Test de Búsqueda
```bash
curl -X POST https://tu-proyecto.railway.app/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "contratos de construcción",
    "project_id": "proyecto_id",
    "top_k": 5
  }'
```

### 3. Verificar Logs
En Railway Dashboard → Tu servicio → **"Logs"**

---

## 📊 Monitoreo y Mantenimiento

### Métricas clave en Railway:
- **CPU Usage**: Modelo de embeddings puede consumir bastante CPU
- **Memory**: Sentence-transformers requiere ~1-2GB RAM
- **Response Time**: Búsquedas vectoriales deberían ser <500ms

### Escalado:
- Railway ofrece planes con más recursos si lo necesitas
- Considera cachear embeddings de queries frecuentes
- Usa índice IVFFlat para búsquedas más rápidas (ya optimizado)

---

## 🐛 Troubleshooting

### Error: "pgvector extension not found"
**Solución**: Ejecuta `CREATE EXTENSION IF NOT EXISTS vector;` en PostgreSQL

### Error: "Module not found"
**Solución**: Verifica que `requirements.txt` tiene todas las dependencias

### Error: "Port already in use"
**Solución**: Railway asigna `$PORT` automáticamente, no hardcodees puertos

### Búsquedas lentas
**Solución**: Verifica que el índice IVFFlat se creó con `lists=470`:
```sql
SELECT * FROM pg_indexes WHERE tablename = 'document_chunks';
```

---

## 📚 Recursos Adicionales

- [Railway Docs](https://docs.railway.app/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Sentence-Transformers Documentation](https://www.sbert.net/)

---

## 🎉 ¡Listo!

Tu sistema RAG está optimizado y listo para producción en Railway con:
- ✅ Índice IVFFlat optimizado (470 lists)
- ✅ Chunks de 2400 caracteres con overlap de 240
- ✅ PostgreSQL + pgvector en la nube
- ✅ Despliegue automatizado desde GitHub
- ✅ Variables de entorno configuradas
- ✅ Healthcheck y monitoring integrado

**URL del backend**: `https://tu-proyecto.railway.app`

---

## 🔗 Próximos Pasos

1. **Frontend**: Desplegar frontend de React en Vercel/Netlify
2. **CORS**: Configurar CORS en FastAPI para permitir requests del frontend
3. **Autenticación**: Agregar auth si es necesario
4. **CI/CD**: Railway auto-deploya en cada push a `main`
5. **Custom Domain**: Configurar dominio personalizado en Railway

---

**Fecha de Optimización**: 2025
**Versión del Sistema**: v2.1 (optimizado para producción)
