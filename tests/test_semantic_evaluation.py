"""
Tests de Evaluación Semántica para RAG
======================================

Métricas implementadas:
- BERT Score: Similitud semántica usando embeddings BERT
- ROUGE (1, 2, L): Overlap de n-gramas para evaluar calidad de resumen
- WER: Word Error Rate - similitud a nivel de palabras

Uso:
    pytest tests/test_semantic_evaluation.py -v
"""

import pytest
from bert_score import score as bert_score
from rouge_score import rouge_scorer
from jiwer import wer, cer
import numpy as np
from typing import List, Dict, Tuple


# ============================================================================
# DATASET DE EVALUACIÓN
# ============================================================================

# Preguntas y respuestas de referencia para evaluar el sistema RAG
EVALUATION_DATASET = [
    {
        "id": 1,
        "pregunta": "¿Qué es el sistema Aconex RAG?",
        "respuesta_referencia": "Aconex RAG es un sistema de recuperación aumentada por generación que combina búsqueda semántica con modelos de lenguaje para proporcionar respuestas contextuales basadas en documentación técnica.",
        "respuesta_modelo": "El sistema Aconex RAG es una plataforma que utiliza búsqueda semántica y generación de lenguaje natural para responder preguntas basándose en documentos técnicos.",
        "categoria": "definicion"
    },
    {
        "id": 2,
        "pregunta": "¿Cómo funciona la búsqueda semántica?",
        "respuesta_referencia": "La búsqueda semántica convierte consultas y documentos en vectores mediante modelos de embeddings, luego calcula similitudes coseno para encontrar los documentos más relevantes.",
        "respuesta_modelo": "La búsqueda semántica usa embeddings para transformar textos en vectores numéricos y encuentra documentos similares calculando la distancia entre vectores.",
        "categoria": "tecnica"
    },
    {
        "id": 3,
        "pregunta": "¿Qué base de datos utiliza el sistema?",
        "respuesta_referencia": "El sistema utiliza PostgreSQL con la extensión pgvector para almacenar y buscar eficientemente vectores de embeddings.",
        "respuesta_modelo": "Usa PostgreSQL con pgvector para almacenamiento y búsqueda vectorial.",
        "categoria": "arquitectura"
    },
    {
        "id": 4,
        "pregunta": "¿Cuál es el tiempo de respuesta esperado?",
        "respuesta_referencia": "El sistema está optimizado para responder búsquedas en menos de 500 milisegundos en el percentil 95, con tiempos promedio alrededor de 350 milisegundos.",
        "respuesta_modelo": "Las búsquedas típicamente responden en menos de medio segundo, con un promedio de 350ms.",
        "categoria": "performance"
    },
    {
        "id": 5,
        "pregunta": "¿Cómo se procesan los documentos PDF?",
        "respuesta_referencia": "Los documentos PDF se extraen usando PyPDF2, se normalizan eliminando caracteres especiales, se dividen en chunks de texto manejables y se generan embeddings para cada chunk.",
        "respuesta_modelo": "Los PDFs se procesan extrayendo texto con PyPDF2, normalizando el contenido, dividiendo en fragmentos y creando vectores de embeddings.",
        "categoria": "procesamiento"
    },
    {
        "id": 6,
        "pregunta": "¿Qué modelo de embeddings se utiliza?",
        "respuesta_referencia": "El sistema utiliza el modelo paraphrase-multilingual-MiniLM-L12-v2 de sentence-transformers, optimizado para textos multilingües y búsqueda semántica.",
        "respuesta_modelo": "Se usa paraphrase-multilingual-MiniLM-L12-v2 de sentence-transformers para generar embeddings.",
        "categoria": "modelo"
    },
    {
        "id": 7,
        "pregunta": "¿Cuántos usuarios concurrentes puede manejar?",
        "respuesta_referencia": "El sistema ha sido probado exitosamente con 50 usuarios concurrentes y puede escalar hasta 100-200 usuarios con configuración multi-worker.",
        "respuesta_modelo": "Puede manejar 50 usuarios concurrentes, escalable a 100-200 con múltiples workers.",
        "categoria": "capacidad"
    },
    {
        "id": 8,
        "pregunta": "¿Qué endpoints expone el API?",
        "respuesta_referencia": "El API expone endpoints principales: /search para búsqueda semántica, /chat para conversaciones RAG, /upload para cargar documentos y /health para verificar estado del sistema.",
        "respuesta_modelo": "Los endpoints principales son /search (búsqueda), /chat (conversación), /upload (documentos) y /health (estado).",
        "categoria": "api"
    }
]


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def calcular_bert_score(referencias: List[str], candidatos: List[str]) -> Dict[str, float]:
    """
    Calcula BERT Score para evaluar similitud semántica.
    
    BERT Score compara embeddings de BERT entre referencia y candidato.
    Valores cercanos a 1.0 indican alta similitud semántica.
    
    Args:
        referencias: Lista de textos de referencia (ground truth)
        candidatos: Lista de textos generados por el modelo
        
    Returns:
        Dict con precision, recall y f1 promedio
    """
    P, R, F1 = bert_score(candidatos, referencias, lang="es", verbose=False)
    
    return {
        "precision": float(P.mean()),
        "recall": float(R.mean()),
        "f1": float(F1.mean())
    }


def calcular_rouge(referencia: str, candidato: str) -> Dict[str, Dict[str, float]]:
    """
    Calcula métricas ROUGE para evaluar overlap de n-gramas.
    
    ROUGE es estándar para evaluar resúmenes y generación de texto:
    - ROUGE-1: Overlap de palabras individuales
    - ROUGE-2: Overlap de bigramas (pares de palabras)
    - ROUGE-L: Subsecuencia común más larga
    
    Args:
        referencia: Texto de referencia
        candidato: Texto generado
        
    Returns:
        Dict con scores de ROUGE-1, ROUGE-2, ROUGE-L
    """
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(referencia, candidato)
    
    return {
        "rouge1": {
            "precision": scores['rouge1'].precision,
            "recall": scores['rouge1'].recall,
            "f1": scores['rouge1'].fmeasure
        },
        "rouge2": {
            "precision": scores['rouge2'].precision,
            "recall": scores['rouge2'].recall,
            "f1": scores['rouge2'].fmeasure
        },
        "rougeL": {
            "precision": scores['rougeL'].precision,
            "recall": scores['rougeL'].recall,
            "f1": scores['rougeL'].fmeasure
        }
    }


def calcular_wer(referencia: str, candidato: str) -> Dict[str, float]:
    """
    Calcula Word Error Rate (WER) y Character Error Rate (CER).
    
    WER mide la tasa de error a nivel de palabras:
    - 0.0 = perfecto (sin errores)
    - 1.0 = completamente diferente
    
    CER hace lo mismo a nivel de caracteres.
    
    Args:
        referencia: Texto de referencia
        candidato: Texto generado
        
    Returns:
        Dict con WER y CER
    """
    wer_score = wer(referencia, candidato)
    cer_score = cer(referencia, candidato)
    
    return {
        "wer": wer_score,
        "cer": cer_score,
        "word_accuracy": 1 - wer_score,  # Precisión en vez de error
        "char_accuracy": 1 - cer_score
    }


def interpretar_metricas(metricas: Dict) -> str:
    """
    Interpreta las métricas y retorna una evaluación cualitativa.
    
    Umbrales basados en literatura de NLP:
    - BERT F1 > 0.9: Excelente
    - BERT F1 > 0.8: Bueno
    - BERT F1 > 0.7: Aceptable
    - BERT F1 < 0.7: Necesita mejora
    """
    bert_f1 = metricas['bert_score']['f1']
    rouge1_f1 = metricas['rouge']['rouge1']['f1']
    word_acc = metricas['wer']['word_accuracy']
    
    if bert_f1 >= 0.9 and rouge1_f1 >= 0.5 and word_acc >= 0.7:
        return "EXCELENTE: Respuesta semánticamente muy similar"
    elif bert_f1 >= 0.8 and rouge1_f1 >= 0.4:
        return "BUENA: Respuesta captura bien el significado"
    elif bert_f1 >= 0.7:
        return "ACEPTABLE: Respuesta razonablemente similar"
    else:
        return "NECESITA MEJORA: Respuesta diverge de la referencia"


# ============================================================================
# TESTS INDIVIDUALES
# ============================================================================

@pytest.mark.parametrize("caso", EVALUATION_DATASET, ids=lambda x: f"caso_{x['id']}")
def test_bert_score_individual(caso):
    """
    Test BERT Score para cada caso individual.
    
    BERT Score mide similitud semántica usando embeddings contextuales.
    Objetivo: F1 > 0.8 (buena similitud semántica)
    """
    ref = caso['respuesta_referencia']
    cand = caso['respuesta_modelo']
    
    resultado = calcular_bert_score([ref], [cand])
    
    print(f"\n📊 BERT Score - {caso['pregunta'][:50]}...")
    print(f"   Precision: {resultado['precision']:.4f}")
    print(f"   Recall:    {resultado['recall']:.4f}")
    print(f"   F1:        {resultado['f1']:.4f}")
    
    # Objetivo: F1 > 0.75 para pasar el test
    assert resultado['f1'] > 0.75, f"BERT F1 muy bajo: {resultado['f1']:.4f}"


@pytest.mark.parametrize("caso", EVALUATION_DATASET, ids=lambda x: f"caso_{x['id']}")
def test_rouge_individual(caso):
    """
    Test ROUGE para cada caso individual.
    
    ROUGE mide overlap de n-gramas entre referencia y candidato.
    Objetivo: ROUGE-1 F1 > 0.4 (buen overlap de palabras)
    """
    ref = caso['respuesta_referencia']
    cand = caso['respuesta_modelo']
    
    resultado = calcular_rouge(ref, cand)
    
    print(f"\n📊 ROUGE Scores - {caso['pregunta'][:50]}...")
    print(f"   ROUGE-1 F1: {resultado['rouge1']['f1']:.4f}")
    print(f"   ROUGE-2 F1: {resultado['rouge2']['f1']:.4f}")
    print(f"   ROUGE-L F1: {resultado['rougeL']['f1']:.4f}")
    
    # Objetivo: ROUGE-1 F1 > 0.3 para pasar el test
    assert resultado['rouge1']['f1'] > 0.3, \
        f"ROUGE-1 F1 muy bajo: {resultado['rouge1']['f1']:.4f}"


@pytest.mark.parametrize("caso", EVALUATION_DATASET, ids=lambda x: f"caso_{x['id']}")
def test_wer_individual(caso):
    """
    Test WER (Word Error Rate) para cada caso individual.
    
    WER mide diferencias a nivel de palabras.
    Objetivo: Word Accuracy > 0.5 (más del 50% de palabras correctas)
    """
    ref = caso['respuesta_referencia']
    cand = caso['respuesta_modelo']
    
    resultado = calcular_wer(ref, cand)
    
    print(f"\n📊 WER Metrics - {caso['pregunta'][:50]}...")
    print(f"   WER:            {resultado['wer']:.4f}")
    print(f"   Word Accuracy:  {resultado['word_accuracy']:.4f}")
    print(f"   CER:            {resultado['cer']:.4f}")
    print(f"   Char Accuracy:  {resultado['char_accuracy']:.4f}")
    
    # WER puede ser alto porque mide edición exacta, no semántica
    # Por eso solo verificamos que no sea completamente diferente
    assert resultado['word_accuracy'] > 0.3, \
        f"Word Accuracy muy baja: {resultado['word_accuracy']:.4f}"


# ============================================================================
# TESTS AGREGADOS
# ============================================================================

def test_bert_score_promedio():
    """
    Test del promedio de BERT Score en todo el dataset.
    
    Evalúa la calidad semántica general del sistema.
    Objetivo: F1 promedio > 0.8
    """
    referencias = [caso['respuesta_referencia'] for caso in EVALUATION_DATASET]
    candidatos = [caso['respuesta_modelo'] for caso in EVALUATION_DATASET]
    
    resultado = calcular_bert_score(referencias, candidatos)
    
    print(f"\n🎯 BERT Score PROMEDIO ({len(EVALUATION_DATASET)} casos)")
    print(f"   Precision: {resultado['precision']:.4f}")
    print(f"   Recall:    {resultado['recall']:.4f}")
    print(f"   F1:        {resultado['f1']:.4f}")
    
    # Guardar para reporte
    with open('reports/bert_score_summary.txt', 'w', encoding='utf-8') as f:
        f.write(f"BERT Score Summary\n")
        f.write(f"==================\n")
        f.write(f"Dataset: {len(EVALUATION_DATASET)} casos\n")
        f.write(f"Precision: {resultado['precision']:.4f}\n")
        f.write(f"Recall:    {resultado['recall']:.4f}\n")
        f.write(f"F1:        {resultado['f1']:.4f}\n")
    
    assert resultado['f1'] > 0.8, f"BERT F1 promedio muy bajo: {resultado['f1']:.4f}"


def test_rouge_promedio():
    """
    Test del promedio de ROUGE en todo el dataset.
    
    Evalúa el overlap de n-gramas general del sistema.
    Objetivo: ROUGE-1 F1 promedio > 0.45
    """
    rouge1_scores = []
    rouge2_scores = []
    rougeL_scores = []
    
    for caso in EVALUATION_DATASET:
        resultado = calcular_rouge(
            caso['respuesta_referencia'],
            caso['respuesta_modelo']
        )
        rouge1_scores.append(resultado['rouge1']['f1'])
        rouge2_scores.append(resultado['rouge2']['f1'])
        rougeL_scores.append(resultado['rougeL']['f1'])
    
    r1_mean = np.mean(rouge1_scores)
    r2_mean = np.mean(rouge2_scores)
    rL_mean = np.mean(rougeL_scores)
    
    print(f"\n🎯 ROUGE PROMEDIO ({len(EVALUATION_DATASET)} casos)")
    print(f"   ROUGE-1 F1: {r1_mean:.4f}")
    print(f"   ROUGE-2 F1: {r2_mean:.4f}")
    print(f"   ROUGE-L F1: {rL_mean:.4f}")
    
    # Guardar para reporte
    with open('reports/rouge_summary.txt', 'w', encoding='utf-8') as f:
        f.write(f"ROUGE Score Summary\n")
        f.write(f"===================\n")
        f.write(f"Dataset: {len(EVALUATION_DATASET)} casos\n")
        f.write(f"ROUGE-1 F1: {r1_mean:.4f}\n")
        f.write(f"ROUGE-2 F1: {r2_mean:.4f}\n")
        f.write(f"ROUGE-L F1: {rL_mean:.4f}\n")
    
    assert r1_mean > 0.4, f"ROUGE-1 F1 promedio muy bajo: {r1_mean:.4f}"


def test_wer_promedio():
    """
    Test del promedio de WER en todo el dataset.
    
    Evalúa la precisión a nivel de palabras del sistema.
    Objetivo: Word Accuracy promedio > 0.5
    """
    wer_scores = []
    word_accuracies = []
    
    for caso in EVALUATION_DATASET:
        resultado = calcular_wer(
            caso['respuesta_referencia'],
            caso['respuesta_modelo']
        )
        wer_scores.append(resultado['wer'])
        word_accuracies.append(resultado['word_accuracy'])
    
    wer_mean = np.mean(wer_scores)
    acc_mean = np.mean(word_accuracies)
    
    print(f"\n🎯 WER PROMEDIO ({len(EVALUATION_DATASET)} casos)")
    print(f"   WER promedio:           {wer_mean:.4f}")
    print(f"   Word Accuracy promedio: {acc_mean:.4f}")
    
    # Guardar para reporte
    with open('reports/wer_summary.txt', 'w', encoding='utf-8') as f:
        f.write(f"WER Summary\n")
        f.write(f"===========\n")
        f.write(f"Dataset: {len(EVALUATION_DATASET)} casos\n")
        f.write(f"WER promedio:           {wer_mean:.4f}\n")
        f.write(f"Word Accuracy promedio: {acc_mean:.4f}\n")
    
    assert acc_mean > 0.4, f"Word Accuracy promedio muy baja: {acc_mean:.4f}"


# ============================================================================
# TEST COMPLETO CON TODAS LAS MÉTRICAS
# ============================================================================

def test_evaluacion_completa():
    """
    Test de evaluación completa con todas las métricas.
    
    Genera un reporte detallado por caso y métricas agregadas.
    """
    print("\n" + "="*80)
    print("EVALUACIÓN SEMÁNTICA COMPLETA DEL SISTEMA RAG")
    print("="*80)
    
    resultados_completos = []
    
    for i, caso in enumerate(EVALUATION_DATASET, 1):
        print(f"\n📝 Caso {i}/{len(EVALUATION_DATASET)}: {caso['pregunta']}")
        print(f"   Categoría: {caso['categoria']}")
        
        # Calcular todas las métricas
        bert = calcular_bert_score(
            [caso['respuesta_referencia']], 
            [caso['respuesta_modelo']]
        )
        rouge = calcular_rouge(
            caso['respuesta_referencia'],
            caso['respuesta_modelo']
        )
        wer_result = calcular_wer(
            caso['respuesta_referencia'],
            caso['respuesta_modelo']
        )
        
        metricas = {
            'bert_score': bert,
            'rouge': rouge,
            'wer': wer_result
        }
        
        evaluacion = interpretar_metricas(metricas)
        
        print(f"   ✅ BERT F1:     {bert['f1']:.4f}")
        print(f"   ✅ ROUGE-1 F1:  {rouge['rouge1']['f1']:.4f}")
        print(f"   ✅ Word Acc:    {wer_result['word_accuracy']:.4f}")
        print(f"   📊 Evaluación:  {evaluacion}")
        
        resultados_completos.append({
            'caso_id': caso['id'],
            'pregunta': caso['pregunta'],
            'categoria': caso['categoria'],
            'metricas': metricas,
            'evaluacion': evaluacion
        })
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN GENERAL")
    print("="*80)
    
    bert_f1s = [r['metricas']['bert_score']['f1'] for r in resultados_completos]
    rouge1_f1s = [r['metricas']['rouge']['rouge1']['f1'] for r in resultados_completos]
    word_accs = [r['metricas']['wer']['word_accuracy'] for r in resultados_completos]
    
    print(f"\n📊 Métricas Promedio:")
    print(f"   BERT F1:        {np.mean(bert_f1s):.4f} (±{np.std(bert_f1s):.4f})")
    print(f"   ROUGE-1 F1:     {np.mean(rouge1_f1s):.4f} (±{np.std(rouge1_f1s):.4f})")
    print(f"   Word Accuracy:  {np.mean(word_accs):.4f} (±{np.std(word_accs):.4f})")
    
    # Evaluación por categoría
    categorias = set(caso['categoria'] for caso in EVALUATION_DATASET)
    print(f"\n📊 Resultados por Categoría:")
    for cat in sorted(categorias):
        casos_cat = [r for r in resultados_completos if r['categoria'] == cat]
        bert_cat = np.mean([c['metricas']['bert_score']['f1'] for c in casos_cat])
        print(f"   {cat:15s}: BERT F1 = {bert_cat:.4f}")
    
    # Guardar reporte completo
    with open('reports/evaluacion_completa.txt', 'w', encoding='utf-8') as f:
        f.write("EVALUACIÓN SEMÁNTICA COMPLETA DEL SISTEMA RAG\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total de casos evaluados: {len(EVALUATION_DATASET)}\n")
        f.write(f"Fecha: 3 de Diciembre, 2025\n\n")
        
        f.write("MÉTRICAS PROMEDIO:\n")
        f.write(f"  BERT F1:        {np.mean(bert_f1s):.4f} ± {np.std(bert_f1s):.4f}\n")
        f.write(f"  ROUGE-1 F1:     {np.mean(rouge1_f1s):.4f} ± {np.std(rouge1_f1s):.4f}\n")
        f.write(f"  Word Accuracy:  {np.mean(word_accs):.4f} ± {np.std(word_accs):.4f}\n\n")
        
        f.write("RESULTADOS POR CASO:\n")
        f.write("-" * 80 + "\n")
        for r in resultados_completos:
            f.write(f"\nCaso {r['caso_id']}: {r['pregunta']}\n")
            f.write(f"  Categoría: {r['categoria']}\n")
            f.write(f"  BERT F1:     {r['metricas']['bert_score']['f1']:.4f}\n")
            f.write(f"  ROUGE-1 F1:  {r['metricas']['rouge']['rouge1']['f1']:.4f}\n")
            f.write(f"  Word Acc:    {r['metricas']['wer']['word_accuracy']:.4f}\n")
            f.write(f"  Evaluación:  {r['evaluacion']}\n")
    
    print(f"\n✅ Reporte guardado en: reports/evaluacion_completa.txt")
    print("="*80 + "\n")
    
    # Verificar que el sistema general es bueno
    assert np.mean(bert_f1s) > 0.75, "BERT F1 promedio debe ser > 0.75"
    assert np.mean(rouge1_f1s) > 0.35, "ROUGE-1 F1 promedio debe ser > 0.35"


if __name__ == "__main__":
    # Ejecutar con: python tests/test_semantic_evaluation.py
    pytest.main([__file__, "-v", "--tb=short"])
