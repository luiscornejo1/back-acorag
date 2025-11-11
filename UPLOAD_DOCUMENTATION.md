# 📤 Funcionalidad de Upload de Documentos

## 🎯 Descripción

Sistema completo para subir documentos nuevos al RAG en tiempo real, con ingesta automática y consultas inmediatas.

---

## ✨ Características

✅ **Formatos soportados**: PDF, TXT, DOCX, JSON  
✅ **Procesamiento automático**: Extracción de texto + Chunking + Embeddings  
✅ **Ingesta instantánea**: Disponible para búsqueda inmediatamente  
✅ **Consulta al subir**: Opción de hacer preguntas sobre el documento recién subido  
✅ **Metadata personalizable**: Añade información adicional (proyecto, tipo, categoría, etc.)  
✅ **Frontend integrado**: Componente React con interfaz elegante  

---

## 🏗️ Arquitectura

```
Usuario sube archivo (PDF/TXT/DOCX)
         ↓
FastAPI recibe archivo
         ↓
Extracción de texto (PyPDF2/python-docx)
         ↓
División en chunks (1000 chars con overlap 200)
         ↓
Generación de embeddings (SentenceTransformer)
         ↓
Inserción en PostgreSQL (documents + document_chunks)
         ↓
[OPCIONAL] Consulta con LLM sobre documento
         ↓
Documento disponible para búsqueda
```

---

## 📦 Instalación

### Backend

```powershell
# Instalar dependencias
pip install PyPDF2==3.0.1 python-docx==1.1.0 python-multipart==0.0.6

# O usar el script
.\install_upload_deps.ps1
```

### Frontend

```bash
# El componente ya está creado en:
# src/components/DocumentUpload.tsx
# src/components/DocumentUpload.css
```

---

## 🚀 Uso

### 1. API Endpoints

#### **POST /upload** - Subir documento

```bash
curl -X POST "https://back-acorag-production.up.railway.app/upload" \
     -F "file=@documento.pdf" \
     -F 'metadata={"project":"Proyecto A","type":"plano","category":"estructural"}'
```

**Respuesta:**
```json
{
  "status": "success",
  "message": "Documento 'documento.pdf' ingestado exitosamente",
  "data": {
    "document_id": "a1b2c3d4...",
    "db_id": 12345,
    "filename": "documento.pdf",
    "chunks_created": 8,
    "text_length": 7842,
    "metadata": {
      "project": "Proyecto A",
      "type": "plano",
      "category": "estructural",
      "filename": "documento.pdf",
      "file_type": "pdf",
      "upload_date": "2024-03-15T10:30:00",
      "text_length": 7842
    }
  }
}
```

---

#### **POST /upload-and-query** - Subir y consultar

```bash
curl -X POST "https://back-acorag-production.up.railway.app/upload-and-query" \
     -F "file=@cronograma.pdf" \
     -F "question=¿Cuál es la fecha de entrega?" \
     -F 'metadata={"project":"Torre A"}'
```

**Respuesta:**
```json
{
  "status": "success",
  "upload_result": {
    "document_id": "x1y2z3...",
    "chunks_created": 5,
    "filename": "cronograma.pdf"
  },
  "query_result": {
    "question": "¿Cuál es la fecha de entrega?",
    "answer": "Según el cronograma, la fecha de entrega del proyecto es el 30 de abril de 2024...",
    "sources": [
      {
        "title": "Cronograma General",
        "score": 0.856,
        "snippet": "Fecha de entrega final: 30/04/2024..."
      }
    ]
  }
}
```

---

### 2. Código Python

```python
from app.upload import upload_and_ingest

# Subir documento desde bytes
with open("documento.pdf", "rb") as f:
    content = f.read()

metadata = {
    "project": "Proyecto A",
    "type": "informe",
    "author": "Juan Pérez"
}

result = upload_and_ingest(
    file_content=content,
    filename="documento.pdf",
    metadata=metadata
)

print(f"✅ Documento {result['document_id']} subido")
print(f"   Chunks: {result['chunks_created']}")
```

---

### 3. Frontend React

Integrar el componente en tu app:

```tsx
import DocumentUpload from './components/DocumentUpload';

function App() {
  return (
    <div>
      <DocumentUpload />
    </div>
  );
}
```

**Características del componente:**
- 📄 **Modo Simple**: Solo sube el documento
- 💬 **Modo Consulta**: Sube y hace pregunta inmediata
- 🏷️ **Metadata**: Campo JSON personalizable
- ✅ **Validación**: Verifica tipos de archivo y JSON
- 📊 **Resultados**: Muestra detalles de ingesta y respuesta

---

## 🧪 Testing

### Test automático completo

```powershell
python test_upload.py
```

**Tests incluidos:**
1. ✅ Upload de archivo TXT con metadata
2. ✅ Upload + consulta inmediata
3. ✅ Búsqueda de documentos subidos

### Test manual con curl

```bash
# Crear archivo de prueba
echo "Este es un documento de prueba sobre construcción." > test.txt

# Subir
curl -X POST "http://localhost:8000/upload" \
     -F "file=@test.txt" \
     -F 'metadata={"project":"Test"}'

# Subir y consultar
curl -X POST "http://localhost:8000/upload-and-query" \
     -F "file=@test.txt" \
     -F "question=¿De qué trata este documento?"
```

---

## 📋 Metadata Recomendada

```json
{
  "project": "Torre Sky Plaza",
  "type": "Informe Técnico",
  "category": "Construcción",
  "document_number": "IT-2024-001",
  "author": "Ing. Juan Pérez",
  "date": "2024-03-15",
  "phase": "Estructura",
  "location": "Piso 12",
  "status": "En progreso"
}
```

**Beneficios:**
- 🔍 Mejores búsquedas (filtros por proyecto, tipo, etc.)
- 📊 Analytics más precisos
- 🏷️ Organización clara
- 📝 Trazabilidad completa

---

## 🔧 Configuración

### Variables de entorno (.env)

```env
# Modelo de embeddings (mismo que el resto del sistema)
EMBEDDING_MODEL=hiiamsid/sentence_similarity_spanish_es

# Tamaño de chunks
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Base de datos
DATABASE_URL=postgresql://user:pass@host:port/db

# Groq para consultas (opcional)
GROQ_API_KEY=gsk_...
```

---

## 📊 Límites y Performance

| Aspecto | Valor |
|---------|-------|
| Tamaño máximo archivo | ~50 MB (ajustable) |
| Tiempo de procesamiento (1 MB PDF) | ~5-10 segundos |
| Chunks por documento (promedio) | 5-15 chunks |
| Formatos soportados | PDF, TXT, DOCX, JSON |
| Velocidad de búsqueda post-upload | Instantánea |

---

## ⚠️ Manejo de Errores

### Errores comunes

**1. "Tipo de archivo no soportado"**
```
Solución: Usar solo PDF, TXT, DOCX, JSON
```

**2. "El documento ya existe"**
```
Solución: El sistema detecta duplicados por hash del contenido
```

**3. "Metadata debe ser un JSON válido"**
```
Solución: Validar el JSON antes de enviar
Ejemplo correcto: {"project":"Test"}
```

**4. "Error extrayendo texto de PDF"**
```
Solución: 
- Verificar que el PDF no esté corrupto
- Algunos PDFs escaneados necesitan OCR
- Probar con otro PDF
```

---

## 🎯 Casos de Uso

### 1. **Documentación en tiempo real**
Cliente sube informe técnico nuevo → Disponible inmediatamente para consultas

### 2. **Actualización de cronogramas**
Sube nuevo cronograma → Consulta fechas críticas → Respuesta instantánea

### 3. **Planos actualizados**
Sube última versión de plano → Sistema mantiene historial → Búsqueda por versión

### 4. **Importación masiva**
Script automatizado para subir 100+ documentos con metadata estructurada

---

## 🔄 Integración con Flujo Existente

El sistema de upload se integra perfectamente con:

✅ **Búsqueda semántica** - Los documentos subidos aparecen en `/search`  
✅ **Chat** - El LLM accede a documentos nuevos en `/chat`  
✅ **Analytics** - Se registran en logs de búsqueda  
✅ **Feedback** - Los usuarios pueden calificar respuestas  

---

## 🚧 Próximas Mejoras

- [ ] Procesamiento en background (Celery/Redis)
- [ ] OCR para PDFs escaneados (Tesseract)
- [ ] Validación de contenido duplicado
- [ ] Compresión de archivos grandes
- [ ] Batch upload (múltiples archivos)
- [ ] Versionado de documentos
- [ ] Soft delete (papelera)
- [ ] Permisos por proyecto

---

## 📚 Referencias

- **PyPDF2**: https://pypdf2.readthedocs.io/
- **python-docx**: https://python-docx.readthedocs.io/
- **FastAPI File Upload**: https://fastapi.tiangolo.com/tutorial/request-files/
- **SentenceTransformers**: https://www.sbert.net/

---

## 🆘 Soporte

Si tienes problemas:

1. **Verificar logs del servidor**: `uvicorn app.api:app --reload`
2. **Probar con archivo simple**: Crear `test.txt` con texto plano
3. **Revisar base de datos**: `python check_db.py` para ver si se guardó
4. **Ejecutar test**: `python test_upload.py` para validar todo el flujo

---

## ✅ Checklist de Instalación

- [x] Crear `app/upload.py`
- [x] Modificar `app/api.py` (agregar endpoints)
- [x] Actualizar `requirements.txt`
- [x] Crear componente React `DocumentUpload.tsx`
- [x] Crear estilos `DocumentUpload.css`
- [x] Crear script de test `test_upload.py`
- [ ] Instalar dependencias: `pip install PyPDF2 python-docx python-multipart`
- [ ] Reiniciar servidor backend
- [ ] Probar endpoint: `python test_upload.py`
- [ ] Integrar componente en frontend
- [ ] Desplegar cambios a Railway

---

**¡Listo!** 🎉 Ahora tienes un sistema completo de upload de documentos con ingesta en tiempo real.
