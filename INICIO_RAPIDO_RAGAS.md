# ⚡ Guía Rápida - Evaluación con RAGAS

## 🎯 ¿Qué es RAGAS?

**RAGAS** (Retrieval Augmented Generation Assessment) es un framework especializado para evaluar sistemas RAG usando métricas específicas:

| Métrica | ¿Qué evalúa? | Rango | Objetivo |
|---------|--------------|-------|----------|
| **Faithfulness** | ¿Respuesta fiel al contexto? | 0-1 | > 0.7 |
| **Answer Relevancy** | ¿Respuesta relevante? | 0-1 | > 0.7 |
| **Context Precision** | ¿Retrieval preciso? | 0-1 | > 0.7 |
| **Context Recall** | ¿Contexto completo? | 0-1 | > 0.7 |
| **Answer Similarity** | Similitud semántica (SemScore) | 0-1 | > 0.7 |
| **Answer Correctness** | ¿Respuesta correcta? | 0-1 | > 0.7 |

---

## 🚀 Inicio Rápido (5 minutos)

### 1. Configurar API Key de OpenAI

RAGAS usa GPT-4 para evaluación (más preciso que métricas tradicionales):

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-tu-api-key-aqui"

# Linux/Mac
export OPENAI_API_KEY="sk-tu-api-key-aqui"

# O crear archivo .env
echo "OPENAI_API_KEY=sk-tu-api-key-aqui" > .env
```

**💡 Obtener API Key:** https://platform.openai.com/api-keys

### 2. Instalar Dependencias

```bash
pip install ragas datasets transformers
```

### 3. Ejecutar Evaluación

```bash
cd backend-acorag

# Evaluación completa
python tests/test_ragas_evaluation.py

# Con pytest
pytest tests/test_ragas_evaluation.py -v
```

### 4. Ver Resultados

```bash
cat reports/ragas_evaluation.txt
```

---

## 📊 Resultados Esperados

```
📊 RESUMEN DE EVALUACIÓN RAGAS
================================================================================
✅ faithfulness              : 0.8500
✅ answer_relevancy          : 0.8200
✅ context_precision         : 0.7800
✅ context_recall            : 0.7600
✅ answer_similarity         : 0.8300
✅ answer_correctness        : 0.8100
================================================================================
```

---

## 🔍 Comparación: RAGAS vs Métricas Básicas

### Métricas Básicas (ya implementadas)

| Métrica | Qué mide | Limitación |
|---------|----------|------------|
| BERT Score | Similitud semántica | No evalúa fidelidad al contexto |
| ROUGE | Coincidencia léxica | No detecta alucinaciones |
| WER | Exactitud literal | Penaliza reformulaciones correctas |

**Resultado:** BERT 0.83, ROUGE-1 0.46 ✅ Sistema comprende bien

### Métricas RAGAS (nuevo)

| Métrica | Qué mide | Ventaja |
|---------|----------|---------|
| Faithfulness | ¿Respuesta fiel a los documentos? | **Detecta alucinaciones** |
| Answer Relevancy | ¿Respuesta relevante a la pregunta? | **Evalúa pertinencia** |
| Context Precision | ¿Documentos recuperados son correctos? | **Evalúa retrieval** |
| Context Recall | ¿Se recuperó toda la info necesaria? | **Evalúa completitud** |
| Answer Similarity | Similitud con respuesta ideal | Similar a BERT Score |

**Resultado:** Evalúa todo el pipeline RAG (retrieval + generation)

---

## 🎯 Casos de Uso

### 1. Detectar Alucinaciones

```python
# Faithfulness < 0.5 → Posibles alucinaciones
pytest tests/test_ragas_evaluation.py::test_ragas_faithfulness -v
```

**Si faithfulness es bajo:**
- El sistema inventa información no presente en documentos
- Acción: Ajustar prompt, limitar creatividad del LLM

### 2. Evaluar Retrieval

```python
# Context Precision < 0.5 → Retrieval recupera documentos irrelevantes
pytest tests/test_ragas_evaluation.py::test_ragas_context_precision -v
```

**Si context_precision es bajo:**
- El sistema recupera documentos no relevantes
- Acción: Mejorar embeddings, ajustar threshold de similitud

### 3. Comparar con Ground Truth

```python
# Answer Similarity → SemScore de Hugging Face
pytest tests/test_ragas_evaluation.py::test_ragas_answer_similarity -v
```

**Comparación:**
- BERT Score (básico): 0.8335
- Answer Similarity (RAGAS): ~0.83
- Ambos deben ser consistentes

---

## 💡 Interpretación de Resultados

### Faithfulness (Fidelidad)

```
0.9-1.0  🟢 EXCELENTE  - Sin alucinaciones
0.7-0.9  🟢 BUENA      - Ocasionalmente añade info
0.5-0.7  🟡 ACEPTABLE  - Algunas inconsistencias
< 0.5    🔴 REVISAR    - Alucinaciones frecuentes
```

**Ejemplo:**
```
Contexto: "El sistema usa PostgreSQL con pgvector"
Respuesta: "El sistema usa PostgreSQL con pgvector"  → Faithfulness: 1.0 ✅
Respuesta: "El sistema usa MongoDB"                  → Faithfulness: 0.0 ❌
```

### Answer Relevancy (Relevancia)

```
0.9-1.0  🟢 EXCELENTE  - Directamente responde la pregunta
0.7-0.9  🟢 BUENA      - Responde con info adicional
0.5-0.7  🟡 ACEPTABLE  - Parcialmente off-topic
< 0.5    🔴 REVISAR    - Respuesta no relacionada
```

**Ejemplo:**
```
Pregunta: "¿Qué base de datos usa?"
Respuesta: "PostgreSQL con pgvector"                     → Relevancy: 1.0 ✅
Respuesta: "El sistema tiene múltiples componentes..."   → Relevancy: 0.6 ⚠️
```

### Context Precision (Precisión del Retrieval)

```
0.9-1.0  🟢 EXCELENTE  - Solo docs relevantes
0.7-0.9  🟢 BUENA      - Mayoría relevantes
0.5-0.7  🟡 ACEPTABLE  - Algo de ruido
< 0.5    🔴 REVISAR    - Demasiados docs irrelevantes
```

**Qué mide:**
- Si los documentos recuperados son realmente relevantes
- Bajo = retrieval recupera mucho ruido

### Context Recall (Completitud)

```
0.9-1.0  🟢 EXCELENTE  - Recuperó toda la info necesaria
0.7-0.9  🟢 BUENA      - Recuperó la mayoría
0.5-0.7  🟡 ACEPTABLE  - Falta alguna info
< 0.5    🔴 REVISAR    - Falta mucha información
```

**Qué mide:**
- Si se recuperaron TODOS los documentos necesarios
- Bajo = retrieval no es exhaustivo

---

## 🔧 Comandos Útiles

### Ejecutar Tests Individuales

```bash
# Solo Faithfulness
pytest tests/test_ragas_evaluation.py::test_ragas_faithfulness -v

# Solo Answer Relevancy
pytest tests/test_ragas_evaluation.py::test_ragas_answer_relevancy -v

# Solo Context Precision
pytest tests/test_ragas_evaluation.py::test_ragas_context_precision -v

# Solo Answer Similarity (SemScore)
pytest tests/test_ragas_evaluation.py::test_ragas_answer_similarity -v
```

### Ver Reportes

```bash
# Reporte completo
cat reports/ragas_evaluation.txt

# CSV para análisis
cat reports/ragas_results.csv
```

---

## 📊 Estructura del Dataset

RAGAS necesita 4 campos para cada caso:

```python
{
    "question": "¿Qué es el sistema?",           # La pregunta del usuario
    "answer": "Es un sistema RAG...",            # Respuesta del sistema
    "contexts": ["Contexto doc 1", "Doc 2"],     # Documentos recuperados
    "ground_truth": "Respuesta ideal..."         # Respuesta de referencia
}
```

**Diferencia con métricas básicas:**
- Métricas básicas: Solo question + answer + ground_truth
- RAGAS: **Incluye contexts** → Puede evaluar el retrieval

---

## ⚠️ Troubleshooting

### Error: "OPENAI_API_KEY not configured"

```bash
# Verificar que esté configurada
echo $env:OPENAI_API_KEY  # Windows
echo $OPENAI_API_KEY      # Linux/Mac

# Si no está, configurarla
$env:OPENAI_API_KEY="sk-..."  # Windows
export OPENAI_API_KEY="sk-..."  # Linux/Mac
```

### Error: "Rate limit exceeded"

RAGAS hace múltiples llamadas a GPT-4. Si tienes límite:

```python
# Usar modelo más barato
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# O evaluar menos casos
RAGAS_DATASET = {...}  # Reducir a 3-5 casos
```

### Evaluación muy lenta

```python
# Evaluar solo algunas métricas
resultado = evaluar_con_ragas(dataset, metricas=[
    faithfulness,        # La más importante
    answer_relevancy,    # También crítica
])
```

---

## 📈 Roadmap

### Ya implementado ✅
- [x] Métricas básicas (BERT, ROUGE, WER)
- [x] RAGAS con 6 métricas
- [x] Dataset de 8 casos

### Próximos pasos 📋
- [ ] Aumentar dataset a 20 casos
- [ ] Integrar evaluación continua (CI/CD)
- [ ] Dashboard visual de métricas
- [ ] Comparación temporal (tracking)

---

## 🔗 Referencias

- [RAGAS Docs](https://docs.ragas.io/)
- [Paper RAGAS](https://arxiv.org/abs/2309.15217)
- [Hugging Face SemScore](https://huggingface.co/spaces/evaluate-metric/semscore)
- [Comparación métricas RAG](https://docs.ragas.io/en/latest/concepts/metrics/index.html)

---

## 📝 Comparación Final

| Aspecto | Métricas Básicas | RAGAS |
|---------|------------------|-------|
| **Evalúa generación** | ✅ Sí | ✅ Sí |
| **Evalúa retrieval** | ❌ No | ✅ Sí |
| **Detecta alucinaciones** | ❌ No | ✅ Sí |
| **Evalúa relevancia** | ⚠️ Parcial | ✅ Sí |
| **Costo** | 🟢 Gratis | 🟡 API OpenAI |
| **Velocidad** | 🟢 Rápido | 🟡 Lento |
| **Precisión** | 🟡 Buena | 🟢 Excelente |

**Recomendación:**
- **Métricas básicas:** Para desarrollo rápido, CI/CD
- **RAGAS:** Para evaluación exhaustiva, pre-deployment

---

**Generado:** Diciembre 2024  
**Tiempo de lectura:** 5 minutos  
**Nivel:** Intermedio
