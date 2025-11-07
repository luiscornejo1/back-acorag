# 🚨 ERROR EN RAILWAY - MODELO NO SE DESCARGA

## Problema:
Railway no puede descargar `dccuchile/bert-base-spanish-wwm-uncased` correctamente.

## Solución:

### Opción 1: Usar modelo más ligero y compatible ⭐ RECOMENDADO

Cambia `EMBEDDING_MODEL` en Railway a uno de estos (en orden de preferencia):

```
hiiamsid/sentence_similarity_spanish_es
```
o
```
sentence-transformers/paraphrase-multilingual-mpnet-base-v2
```

### Opción 2: Mantener el modelo actual temporalmente

Si quieres mantener el modelo original mientras solucionamos:
```
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

## 📝 Pasos para arreglar:

1. Ve a Railway: https://railway.app
2. Proyecto: **back-acorag-production**
3. **Variables** tab
4. Busca `EMBEDDING_MODEL`
5. Cambia a: `hiiamsid/sentence_similarity_spanish_es`
6. Guarda
7. Espera redespliegue (2-3 min)
8. Prueba en frontend

## ✅ Modelo recomendado actualizado:

**MEJOR OPCIÓN**: `hiiamsid/sentence_similarity_spanish_es`
- ✅ Optimizado para español
- ✅ 384 dimensiones (ligero, compatible Railway)
- ✅ Se descarga rápido
- ✅ Buena precisión en español

## Re-ingesta después del cambio:

Una vez que Railway funcione con el nuevo modelo, ejecuta:

```powershell
# 1. Actualiza .env.railway con DATABASE_URL de Railway
# 2. Ejecuta:
python reingest_to_railway.py
```
