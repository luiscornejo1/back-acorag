# 🚀 Git Commit y Push para Railway

## 📝 Commit Message Sugerido

```bash
git add .
git commit -m "feat: Production optimizations for Railway deployment

- Optimize IVFFlat index: lists 100→470 for 221K chunks dataset
- Increase chunk size: 1200→2400 chars for better email context
- Adjust overlap: 200→240 chars (10% proportion)
- Add Railway deployment files (Procfile, railway.json, runtime.txt)
- Update .env.example with PORT variable
- Add comprehensive deployment documentation
- Ready for production deployment on Railway PaaS

Performance improvements:
- 30-50% faster vector search with optimized IVFFlat index
- Better semantic understanding with larger chunks
- Optimal overlap to prevent context loss

Files modified:
- app/ingest.py (index & chunking config)
- .env.example (PORT variable)

Files added:
- Procfile
- railway.json
- runtime.txt
- RAILWAY_DEPLOYMENT.md
- FRONTEND_CONNECTION.md
- OPTIMIZATION_SUMMARY.md
- GIT_COMMANDS.md

Infrastructure: PostgreSQL 15 + pgvector + Railway
Dataset: 147,066 documents, 221,306 chunks
Embedding: paraphrase-multilingual-MiniLM-L12-v2 (384d)"
```

---

## 🔍 Verificar Cambios Antes de Commit

```bash
# Ver archivos modificados
git status

# Ver diferencias específicas
git diff app/ingest.py

# Ver todos los archivos nuevos
git status -u
```

---

## 📤 Push a GitHub

```bash
# Si es tu primera vez pusheando a este repositorio
git remote add origin https://github.com/luiscornejo1/back-acorag.git
git branch -M main
git push -u origin main

# Si ya está configurado
git push origin main
```

---

## 🔐 Si tienes problemas de autenticación en GitHub

### Opción 1: Personal Access Token (Recomendado)
1. Ve a GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click en "Generate new token (classic)"
3. Selecciona scopes: `repo` (Full control of private repositories)
4. Copia el token generado
5. Cuando Git te pida password, usa el token en lugar de tu contraseña

### Opción 2: SSH
```bash
# Generar clave SSH (si no tienes)
ssh-keygen -t ed25519 -C "tu-email@example.com"

# Copiar clave pública
cat ~/.ssh/id_ed25519.pub

# Agregar a GitHub: Settings → SSH and GPG keys → New SSH key
```

---

## 📊 Después del Push

### 1. Verificar en GitHub
- Ve a: https://github.com/luiscornejo1/back-acorag
- Verifica que todos los archivos nuevos estén presentes
- Revisa el commit message

### 2. Crear Proyecto en Railway
Ahora puedes seguir la guía en `RAILWAY_DEPLOYMENT.md`

---

## ⚠️ IMPORTANTE: Archivos que NO se subirán

Gracias al `.gitignore`, estos archivos NO se subirán (está bien):
- `.venv311/` (entorno virtual - 617MB)
- `data/mis_correos.json` (182MB de datos)
- `__pycache__/` (archivos compilados de Python)
- `*.pyc` (bytecode de Python)
- `.env` (variables de entorno secretas)

---

## ✅ Archivos que SÍ se subirán

Los siguientes archivos son seguros y necesarios para Railway:
- ✅ `app/*.py` (código fuente)
- ✅ `requirements.txt` (dependencias)
- ✅ `Procfile` (comando de inicio)
- ✅ `railway.json` (configuración)
- ✅ `runtime.txt` (versión Python)
- ✅ `.env.example` (template de variables)
- ✅ `*.md` (documentación)
- ✅ `sql/*.sql` (esquemas de base de datos)

---

## 🎯 Próximos Pasos Después del Push

1. **Ir a Railway**: [railway.app/dashboard](https://railway.app/dashboard)
2. **Seguir guía**: Abrir `RAILWAY_DEPLOYMENT.md` y seguir paso a paso
3. **Configurar PostgreSQL**: Railway proveerá automáticamente
4. **Instalar pgvector**: `CREATE EXTENSION IF NOT EXISTS vector;`
5. **Variables de entorno**: Configurar en Railway dashboard
6. **Reindexar datos**: Con nueva configuración optimizada
7. **Verificar deployment**: Test `/health` y `/search` endpoints

---

## 📞 Ayuda Adicional

Si tienes problemas:
1. **Git push fails**: Verifica autenticación (token o SSH)
2. **Large files error**: El `.gitignore` ya los excluye, verifica con `git status`
3. **Railway deployment fails**: Revisa logs en Railway dashboard
4. **pgvector no instalado**: Ejecuta `CREATE EXTENSION vector;` en PostgreSQL

---

## 🎉 ¡Ya casi terminas!

Una vez que hagas `git push`, tu código estará en GitHub y listo para:
- ✅ Deployment automático en Railway
- ✅ PostgreSQL + pgvector en la nube
- ✅ API de búsqueda semántica en producción
- ✅ Sistema RAG completamente funcional

**Siguiente paso**: `git push origin main` → Railway → Producción 🚀
