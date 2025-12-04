# 🎯 Cómo Evaluar Aconex RAG con RAGAS y SemScore

## 📊 Estado Actual

### ✅ Ya Implementado

1. **Métricas Básicas NLP** (Completado)
   - BERT Score: 0.8335 ✅
   - ROUGE-1: 0.4558 ✅
   - Word Accuracy: 0.2237 ⚠️ (Normal en RAG)
   - Archivo: `tests/test_semantic_evaluation.py`
   - Reportes: `reports/*.txt`

2. **Framework RAGAS** (Implementado, pendiente ejecutar)
   - Faithfulness (detecta alucinaciones)
   - Answer Relevancy (relevancia de respuestas)
   - Context Precision (calidad del retrieval)
   - Context Recall (completitud)
   - Answer Similarity (SemScore de Hugging Face)
   - Archivo: `tests/test_ragas_evaluation.py`

---

## 🚀 Cómo Usar RAGAS (Paso a Paso)

### Paso 1: Obtener API Key de OpenAI

**¿Por qué necesito esto?**
- RAGAS usa GPT-4 para evaluar las respuestas (más preciso que métricas automáticas)
- El costo es mínimo: ~$0.50 para 100 evaluaciones

**Cómo obtenerla:**
1. Ve a https://platform.openai.com/api-keys
2. Crea una cuenta o inicia sesión
3. Click en "Create new secret key"
4. Copia la key (empieza con `sk-...`)

### Paso 2: Configurar la API Key

**Opción A: Variable de entorno (temporal)**
```powershell
# En PowerShell
$env:OPENAI_API_KEY="sk-tu-api-key-aqui"
```

**Opción B: Archivo .env (permanente)**
```bash
# Crear archivo .env en backend-acorag/
cd backend-acorag
echo "OPENAI_API_KEY=sk-tu-api-key-aqui" > .env
```

### Paso 3: Ejecutar Evaluación RAGAS

```bash
cd backend-acorag

# Opción 1: Script directo (más rápido)
python tests/test_ragas_evaluation.py

# Opción 2: Con pytest (más detallado)
pytest tests/test_ragas_evaluation.py -v
```

**Tiempo estimado:** 2-5 minutos (depende de API de OpenAI)

### Paso 4: Ver Resultados

```bash
# Reporte completo
cat reports/ragas_evaluation.txt

# CSV para análisis
cat reports/ragas_results.csv
```

---

## 📊 Qué Esperar de los Resultados

### Métricas RAGAS Explicadas

#### 1. Faithfulness (Fidelidad)
```
¿Qué mide? ¿La respuesta es fiel a los documentos recuperados?
Objetivo: > 0.7
Detecta: Alucinaciones (sistema inventa información)

Ejemplo:
Contexto: "El sistema usa PostgreSQL"
Respuesta: "El sistema usa PostgreSQL"     → 1.0 ✅
Respuesta: "El sistema usa MongoDB"        → 0.0 ❌ (alucinación)
```

**Si es bajo (< 0.5):**
- El sistema está inventando información
- Acción: Ajustar prompt para ser más fiel a contexto

#### 2. Answer Relevancy (Relevancia)
```
¿Qué mide? ¿La respuesta es relevante a la pregunta?
Objetivo: > 0.7
Detecta: Respuestas off-topic

Ejemplo:
Pregunta: "¿Qué base de datos usa?"
Respuesta: "PostgreSQL con pgvector"                    → 1.0 ✅
Respuesta: "El sistema tiene múltiples componentes..."  → 0.5 ⚠️
```

**Si es bajo (< 0.5):**
- El sistema responde cosas no relacionadas
- Acción: Mejorar prompt, ajustar retrieval

#### 3. Context Precision (Precisión del Retrieval)
```
¿Qué mide? ¿Los documentos recuperados son relevantes?
Objetivo: > 0.7
Detecta: Ruido en resultados de búsqueda

Ejemplo:
Pregunta: "¿Qué base de datos usa?"
Contextos recuperados:
  1. "PostgreSQL con pgvector"              → Relevante ✅
  2. "API endpoints disponibles"            → No relevante ❌
Context Precision = 0.5 (50% relevantes)
```

**Si es bajo (< 0.5):**
- El retrieval recupera muchos documentos irrelevantes
- Acción: Ajustar threshold de similitud, mejorar embeddings

#### 4. Context Recall (Completitud)
```
¿Qué mide? ¿Se recuperaron TODOS los docs necesarios?
Objetivo: > 0.7
Detecta: Información faltante

Ejemplo:
Ground truth menciona: "PostgreSQL", "pgvector", "embeddings"
Contextos recuperados mencionan: "PostgreSQL", "pgvector"
Context Recall = 0.67 (falta "embeddings")
```

**Si es bajo (< 0.5):**
- El retrieval no encuentra toda la información necesaria
- Acción: Aumentar k (número de documentos recuperados)

#### 5. Answer Similarity (SemScore)
```
¿Qué mide? Similitud semántica con respuesta ideal
Objetivo: > 0.7
Detecta: Qué tan similar es a la respuesta perfecta

Es equivalente a BERT Score que ya implementamos.
Nuestro BERT Score: 0.8335 ✅
```

---

## 🎯 Comparación: Métricas Básicas vs RAGAS

### Lo que ya tienes (Métricas Básicas)

```
RESULTADOS ACTUALES:
✅ BERT F1:        0.8335  (Excelente similitud semántica)
✅ ROUGE-1:        0.4558  (Buena cobertura léxica)
✅ ROUGE-L:        0.4097  (Buena estructura)
⚠️ Word Accuracy:  0.2237  (Reformulación - normal en RAG)

CONCLUSIÓN: El sistema COMPRENDE bien y usa vocabulario apropiado
```

**Limitaciones:**
- ❌ No evalúan el retrieval (solo la generación)
- ❌ No detectan alucinaciones
- ❌ No miden relevancia de respuestas

### Lo que vas a obtener (RAGAS)

```
RESULTADOS ESPERADOS:
✅ Faithfulness:        0.85  (Sin alucinaciones)
✅ Answer Relevancy:    0.82  (Respuestas relevantes)
✅ Context Precision:   0.78  (Retrieval preciso)
✅ Context Recall:      0.76  (Recupera info completa)
✅ Answer Similarity:   0.83  (Similar a BERT Score)
```

**Ventajas:**
- ✅ Evalúa TODO el pipeline RAG (retrieval + generation)
- ✅ Detecta alucinaciones
- ✅ Mide calidad del retrieval
- ✅ Más preciso (usa GPT-4 para evaluación)

---

## 💡 Interpretación de Resultados

### Escenario 1: Todo está bien ✅

```
Faithfulness:      0.85  ✅
Answer Relevancy:  0.82  ✅
Context Precision: 0.78  ✅
Context Recall:    0.76  ✅
Answer Similarity: 0.83  ✅
```

**Interpretación:**
- El sistema funciona excelentemente
- No hay alucinaciones
- Retrieval es efectivo
- Respuestas son relevantes y similares a las ideales

**Acción:** Mantener y monitorear

### Escenario 2: Problema de Alucinaciones ⚠️

```
Faithfulness:      0.45  ❌ Bajo
Answer Relevancy:  0.80  ✅ OK
Context Precision: 0.75  ✅ OK
Context Recall:    0.70  ✅ OK
Answer Similarity: 0.50  ⚠️ Bajo
```

**Interpretación:**
- El retrieval funciona bien
- PERO el sistema inventa información no presente en documentos
- Las respuestas son relevantes pero incorrectas

**Acción:**
1. Ajustar prompt: "Responde SOLO con información del contexto"
2. Reducir temperatura del LLM (más conservador)
3. Añadir validación: "Si no sabes, di 'No tengo esa información'"

### Escenario 3: Problema de Retrieval ⚠️

```
Faithfulness:      0.85  ✅ OK
Answer Relevancy:  0.80  ✅ OK
Context Precision: 0.40  ❌ Bajo
Context Recall:    0.35  ❌ Bajo
Answer Similarity: 0.70  ⚠️ Moderado
```

**Interpretación:**
- El LLM genera bien (es fiel al contexto que recibe)
- PERO el retrieval no encuentra los documentos correctos
- Recupera documentos irrelevantes o incompletos

**Acción:**
1. Mejorar embeddings: Usar modelo más grande o fine-tuned
2. Ajustar k: Recuperar más documentos (ej: k=5 en vez de k=3)
3. Ajustar threshold: Bajar umbral de similitud
4. Re-indexar documentos: Mejorar chunking

### Escenario 4: Problema de Relevancia ⚠️

```
Faithfulness:      0.85  ✅ OK
Answer Relevancy:  0.45  ❌ Bajo
Context Precision: 0.75  ✅ OK
Context Recall:    0.70  ✅ OK
Answer Similarity: 0.60  ⚠️ Moderado
```

**Interpretación:**
- Retrieval funciona
- Respuestas son fieles
- PERO respuestas no son directas (mucha info extra)

**Acción:**
1. Mejorar prompt: "Responde directamente y de forma concisa"
2. Ajustar system message
3. Post-procesar respuestas para hacerlas más directas

---

## 📈 Flujo de Trabajo Recomendado

### 1. Primera Evaluación (Ahora)

```bash
# Ejecutar métricas básicas (ya hecho)
pytest tests/test_semantic_evaluation.py -v

# Ejecutar RAGAS (nuevo)
python tests/test_ragas_evaluation.py
```

**Resultado:** Baseline para comparar futuras mejoras

### 2. Identificar Problemas

```bash
# Ver reportes
cat reports/ragas_evaluation.txt

# Identificar métricas bajas
# Si Faithfulness < 0.7 → Problema de alucinaciones
# Si Context Precision < 0.7 → Problema de retrieval
# Si Answer Relevancy < 0.7 → Problema de generación
```

### 3. Implementar Mejoras

Según los problemas identificados:
- Ajustar prompts
- Mejorar embeddings
- Cambiar parámetros (k, threshold)
- Re-indexar documentos

### 4. Re-evaluar

```bash
# Ejecutar de nuevo
python tests/test_ragas_evaluation.py

# Comparar con baseline
# ¿Las métricas mejoraron?
```

### 5. Iterar

Repetir pasos 2-4 hasta alcanzar objetivos

---

## 🎯 Objetivos de Métricas

### Mínimo (Pre-producción)
```
Faithfulness:      > 0.70  ✅
Answer Relevancy:  > 0.70  ✅
Context Precision: > 0.60  ⚠️ (Puede haber algo de ruido)
Context Recall:    > 0.60  ⚠️ (Puede faltar alguna info)
Answer Similarity: > 0.70  ✅
```

### Ideal (Producción)
```
Faithfulness:      > 0.85  🎯
Answer Relevancy:  > 0.80  🎯
Context Precision: > 0.75  🎯
Context Recall:    > 0.75  🎯
Answer Similarity: > 0.80  🎯
```

### Excelente (Estado del arte)
```
Faithfulness:      > 0.90  ⭐
Answer Relevancy:  > 0.85  ⭐
Context Precision: > 0.85  ⭐
Context Recall:    > 0.85  ⭐
Answer Similarity: > 0.85  ⭐
```

---

## 🔧 Troubleshooting

### "OPENAI_API_KEY not configured"

```powershell
# Verificar
$env:OPENAI_API_KEY

# Si está vacío, configurar
$env:OPENAI_API_KEY="sk-tu-key-aqui"
```

### "Rate limit exceeded"

```python
# Opción 1: Usar modelo más barato
llm = ChatOpenAI(model="gpt-4o-mini")  # En vez de gpt-4

# Opción 2: Reducir dataset
# Editar tests/test_ragas_evaluation.py
# Usar solo 3-5 casos en vez de 8
```

### Evaluación muy lenta

```python
# Evaluar solo métricas críticas
metricas = [
    faithfulness,      # Más importante
    answer_relevancy,  # También crítica
]
```

---

## 📚 Documentación Generada

### Archivos Creados

1. **`tests/test_ragas_evaluation.py`** (590 líneas)
   - Script completo de evaluación RAGAS
   - 6 métricas implementadas
   - Tests individuales por métrica

2. **`INICIO_RAPIDO_RAGAS.md`**
   - Guía rápida para ejecutar
   - Interpretación de métricas
   - Comandos útiles

3. **`COMO_USAR_RAGAS.md`** (este archivo)
   - Guía completa paso a paso
   - Comparaciones y ejemplos
   - Troubleshooting

### Reportes que se Generan

Después de ejecutar, se crean:
- `reports/ragas_evaluation.txt` - Reporte completo
- `reports/ragas_results.csv` - Datos para análisis

---

## 🎉 Próximos Pasos

### Inmediato (Hoy)
1. ✅ Configurar OPENAI_API_KEY
2. ✅ Ejecutar `python tests/test_ragas_evaluation.py`
3. ✅ Revisar `reports/ragas_evaluation.txt`

### Corto Plazo (Esta semana)
4. 📋 Comparar resultados RAGAS con métricas básicas
5. 📋 Identificar áreas de mejora
6. 📋 Documentar hallazgos

### Mediano Plazo (Próximo mes)
7. 📋 Implementar mejoras basadas en resultados
8. 📋 Re-evaluar y comparar
9. 📋 Integrar en CI/CD

---

## 💰 Costo Estimado

**RAGAS con OpenAI API:**
- Modelo: gpt-4o-mini (más barato)
- Costo: ~$0.15 por token output
- Evaluación completa (8 casos): ~$0.30-0.50
- 100 evaluaciones: ~$5-10

**Comparación:**
- Métricas básicas (BERT, ROUGE): Gratis pero menos precisas
- RAGAS: Bajo costo pero muy preciso

**Recomendación:**
- Desarrollo: Usa métricas básicas (gratis, rápido)
- Pre-deployment: Usa RAGAS (preciso, detecta problemas)
- Producción: Combina ambos (CI con básicas, audit con RAGAS)

---

## 🔗 Referencias

- [RAGAS Documentación](https://docs.ragas.io/)
- [Paper RAGAS](https://arxiv.org/abs/2309.15217)
- [SemScore Hugging Face](https://huggingface.co/spaces/evaluate-metric/semscore)
- [Métricas Básicas](./PRUEBAS_SEMANTICAS_RAG.md)

---

**Generado:** Diciembre 2024  
**Estado:** ✅ Listo para ejecutar  
**Próximo paso:** Configurar OPENAI_API_KEY y correr evaluación
