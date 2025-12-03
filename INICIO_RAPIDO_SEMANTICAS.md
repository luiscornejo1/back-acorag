# ⚡ Guía Rápida - Pruebas Semánticas RAG

## 🎯 ¿Qué son estas pruebas?

Evalúan la **calidad de las respuestas** del sistema RAG usando 3 métricas:

1. **BERT Score** → ¿El significado es correcto? 🧠
2. **ROUGE** → ¿Usa las palabras apropiadas? 📝
3. **WER** → ¿Qué tan diferente es del texto original? 🔍

---

## 🚀 Inicio Rápido (2 minutos)

### 1. Instalar Dependencias

```bash
pip install bert-score rouge-score jiwer pytest
```

### 2. Ejecutar Pruebas

```bash
cd backend-acorag
pytest tests/test_semantic_evaluation.py -v
```

### 3. Ver Resultados

```bash
cat reports/evaluacion_completa.txt
```

---

## 📊 Resultados Actuales

```
✅ BERT F1:        0.8335  (Excelente similitud semántica)
✅ ROUGE-1 F1:     0.4558  (Buena cobertura léxica)
✅ ROUGE-2 F1:     0.2022  (Bigramas consistentes)
✅ ROUGE-L F1:     0.4097  (Buena estructura)
⚠️ Word Accuracy:  0.2237  (Reformulación - normal en RAG)

VEREDICTO: ✅ SISTEMA APROBADO
```

---

## 🎯 Interpretación Simple

### ✅ ¿El sistema funciona bien?

**SÍ** → BERT Score = 0.83 (Excelente)

El sistema comprende las preguntas y genera respuestas correctas.

### ⚠️ ¿Por qué Word Accuracy es baja?

**Es NORMAL** → Los sistemas RAG reformulan información

```
No copia literal → Genera respuestas originales
BERT alto (0.83) → El significado es correcto
→ No hay problema ✅
```

---

## 📚 Documentación Completa

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| [RESUMEN_EJECUTIVO_SEMANTICAS.md](./RESUMEN_EJECUTIVO_SEMANTICAS.md) | Dashboard con métricas | 1 página |
| [PRUEBAS_SEMANTICAS_RAG.md](./PRUEBAS_SEMANTICAS_RAG.md) | Guía completa técnica | 50+ páginas |
| [tests/test_semantic_evaluation.py](./tests/test_semantic_evaluation.py) | Código de las pruebas | Script Python |

---

## 🔧 Comandos Útiles

### Ver solo BERT Score
```bash
pytest tests/test_semantic_evaluation.py::test_bert_score_promedio -v
```

### Ver solo ROUGE
```bash
pytest tests/test_semantic_evaluation.py::test_rouge_promedio -v
```

### Ver solo WER
```bash
pytest tests/test_semantic_evaluation.py::test_wer_promedio -v
```

### Generar reporte completo
```bash
pytest tests/test_semantic_evaluation.py::test_evaluacion_completa -v
```

---

## 📈 ¿Qué métrica importa más?

### Para usuarios técnicos:
**BERT Score** → Mide si el sistema entiende correctamente

### Para usuarios de negocio:
**ROUGE-1** → Mide si usa el vocabulario técnico apropiado

### Para desarrolladores:
**WER** → Mide cuánto reformula (alto = no copia literal)

---

## ✅ Checklist de Calidad

| Métrica | Umbral | Actual | Estado |
|---------|--------|--------|--------|
| BERT F1 | > 0.75 | **0.83** | ✅ |
| ROUGE-1 | > 0.30 | **0.46** | ✅ |
| ROUGE-2 | > 0.15 | **0.20** | ✅ |
| ROUGE-L | > 0.25 | **0.41** | ✅ |

**RESULTADO: 4/4 APROBADAS** ✅

---

## 🚨 Cuándo Preocuparse

### 🔴 Alerta Roja (Acción inmediata)
- BERT F1 < 0.70 → El sistema no comprende
- ROUGE-1 < 0.25 → Vocabulario incorrecto

### 🟡 Alerta Amarilla (Revisar)
- BERT F1 < 0.75 → Revisar casos problemáticos
- ROUGE-1 < 0.30 → Mejorar cobertura léxica

### 🟢 Estado Saludable (Actual)
- BERT F1 > 0.80 → ✅ Excelente comprensión
- ROUGE-1 > 0.40 → ✅ Buen vocabulario

---

## 💡 Próximos Pasos

1. ✅ **Sistema aprobado** - Listo para producción
2. 📋 Configurar monitoreo continuo
3. 📋 Recopilar feedback de usuarios
4. 📋 Expandir dataset de evaluación (20-30 casos)

---

## 🔗 Enlaces Rápidos

- 📊 [Ver reporte completo](./reports/evaluacion_completa.txt)
- 📈 [Dashboard ejecutivo](./RESUMEN_EJECUTIVO_SEMANTICAS.md)
- 📚 [Documentación técnica](./PRUEBAS_SEMANTICAS_RAG.md)
- 🧪 [Código de pruebas](./tests/test_semantic_evaluation.py)

---

**Generado:** Diciembre 2024  
**Tiempo de lectura:** 2 minutos  
**Nivel:** Principiante-Intermedio
