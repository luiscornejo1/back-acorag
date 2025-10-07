# 🔗 Conectar Frontend con Backend en Railway

## 📝 Configuración del Frontend

Una vez que tu backend esté desplegado en Railway, necesitarás actualizar el frontend para apuntar a la nueva URL de producción.

### Paso 1: Obtener URL de Railway

1. Ve a tu proyecto en [Railway Dashboard](https://railway.app/dashboard)
2. Click en tu servicio backend
3. Ve a **"Settings" → "Networking"**
4. Encontrarás tu URL pública, algo como:
   ```
   https://back-acorag-production.up.railway.app
   ```

### Paso 2: Actualizar API URL en Frontend

Edita `frontend-acorag/src/api.ts`:

```typescript
// Cambia la URL base de desarrollo a producción
const API_BASE_URL = 'https://tu-proyecto.railway.app';  // ← Actualiza aquí

export const searchDocuments = async (query: string, projectId: string, topK: number = 5) => {
  const response = await fetch(`${API_BASE_URL}/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      project_id: projectId,
      top_k: topK,
    }),
  });

  if (!response.ok) {
    throw new Error('Error en la búsqueda');
  }

  return response.json();
};
```

### Paso 3: Variables de Entorno (Recomendado)

Para manejar diferentes entornos (desarrollo/producción), crea un archivo `.env`:

**`.env.production`** (para producción):
```bash
VITE_API_BASE_URL=https://tu-proyecto.railway.app
```

**`.env.development`** (para local):
```bash
VITE_API_BASE_URL=http://localhost:8000
```

Luego actualiza `api.ts`:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

### Paso 4: Build y Deploy del Frontend

#### Opción A: Vercel (Recomendado)
1. Push tu frontend a GitHub (repositorio separado o mismo repo)
2. Ve a [vercel.com](https://vercel.com)
3. Click en **"New Project"**
4. Importa tu repositorio
5. Configura:
   - **Framework**: Vite
   - **Root Directory**: `frontend-acorag`
   - **Environment Variables**: Agrega `VITE_API_BASE_URL`
6. Deploy!

#### Opción B: Netlify
Similar a Vercel:
1. Ve a [netlify.com](https://netlify.com)
2. Click en **"Add new site" → "Import an existing project"**
3. Selecciona tu repositorio
4. Configura:
   - **Base directory**: `frontend-acorag`
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`
   - **Environment variables**: Agrega `VITE_API_BASE_URL`

#### Opción C: Railway (Frontend también)
1. En tu proyecto de Railway, click **"+ New"**
2. Selecciona **"GitHub Repo"**
3. Configura:
   - **Root Directory**: `frontend-acorag`
   - **Build Command**: `npm run build`
   - **Start Command**: `npm run preview`

---

## 🔒 Configurar CORS (Ya está listo)

El backend ya tiene CORS configurado en `app/api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ← Cambia a tu dominio específico en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Para producción**, actualiza `allow_origins` con tu dominio de frontend:

```python
allow_origins=[
    "https://tu-frontend.vercel.app",
    "http://localhost:5173",  # Para desarrollo local
],
```

Luego redespliega el backend en Railway (automático si usas GitHub).

---

## 🧪 Verificar Conexión Frontend-Backend

1. Abre las **DevTools** de tu navegador (F12)
2. Ve a la pestaña **"Network"**
3. Realiza una búsqueda en tu frontend
4. Deberías ver una request a `https://tu-proyecto.railway.app/search`
5. Verifica que el status code sea `200 OK`

---

## 📊 Arquitectura Final

```
┌─────────────────────────────────────────┐
│  Frontend (React + TypeScript + Vite)  │
│  Desplegado en: Vercel/Netlify         │
│  URL: https://tu-frontend.vercel.app   │
└─────────────────┬───────────────────────┘
                  │
                  │ HTTPS Requests
                  │
┌─────────────────▼───────────────────────┐
│  Backend (FastAPI + Python)            │
│  Desplegado en: Railway                │
│  URL: https://tu-proyecto.railway.app  │
└─────────────────┬───────────────────────┘
                  │
                  │ PostgreSQL Connection
                  │
┌─────────────────▼───────────────────────┐
│  PostgreSQL + pgvector                 │
│  Desplegado en: Railway                │
│  221,306 chunks indexados              │
│  IVFFlat Index (lists=470)             │
└─────────────────────────────────────────┘
```

---

## 🎉 ¡Listo!

Tu aplicación RAG completa está en la nube:
- ✅ Backend optimizado en Railway
- ✅ Frontend responsivo en Vercel/Netlify
- ✅ Base de datos PostgreSQL + pgvector
- ✅ CORS configurado correctamente
- ✅ Variables de entorno por ambiente
- ✅ Despliegue continuo desde GitHub

**URLs finales**:
- **Frontend**: `https://tu-frontend.vercel.app`
- **Backend**: `https://tu-proyecto.railway.app`
- **API Docs**: `https://tu-proyecto.railway.app/docs`

---

## 🔗 Recursos

- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [Vercel Deployment](https://vercel.com/docs)
- [Netlify Deployment](https://docs.netlify.com/)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
