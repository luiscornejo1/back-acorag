"""
Evaluación RAG usando RAGAS Framework con OpenAI
=================================================

Este script evalúa el sistema Aconex RAG usando métricas RAGAS:
- Faithfulness: ¿La respuesta es fiel al contexto recuperado?
- Answer Relevancy: ¿La respuesta es relevante a la pregunta?
- Context Precision: ¿El contexto recuperado es preciso?
- Context Recall: ¿El contexto recuperado es completo?
- Answer Semantic Similarity: Similitud semántica (SemScore)
- Answer Correctness: Corrección general

CONFIGURACIÓN:
1. Obtener API key gratis en: https://platform.openai.com/api-keys
2. Configurar: $env:OPENAI_API_KEY="sk-proj-tu-key-aqui"
3. Costo estimado: $0.10-0.30 USD con GPT-4o-mini para 8 casos

Documentación: https://docs.ragas.io/
"""

import os
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_similarity,
    answer_correctness
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import pandas as pd
from datetime import datetime
import numpy as np

# =============================================================================
# CONFIGURACIÓN OPENAI
# =============================================================================

# Modelo LLM para evaluación (GPT-4o-mini es más económico)
llm = ChatOpenAI(
    model="gpt-4o-mini",  # Más barato: $0.15/1M tokens entrada, $0.60/1M salida
    temperature=0
)

# Embeddings de OpenAI
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"  # Más económico que ada-002
)

# =============================================================================
# DATASET DE EVALUACIÓN PARA RAGAS
# =============================================================================

# Formato RAGAS: question, answer, contexts, ground_truth
RAGAS_DATASET = {
    "question": [
        "¿Qué es el sistema Aconex RAG?",
        "¿Cómo funciona la búsqueda semántica en el sistema?",
        "¿Qué base de datos utiliza el sistema?",
        "¿Cuál es el tiempo de respuesta esperado del sistema?",
        "¿Cómo se procesan los documentos PDF?",
        "¿Qué modelo de embeddings se utiliza?",
        "¿Cuántos usuarios concurrentes puede manejar el sistema?",
        "¿Qué endpoints expone el API?",
    ],
    "answer": [
        # Respuestas generadas por el sistema RAG
        "El sistema Aconex RAG es una solución de búsqueda y generación aumentada que integra vectorización semántica con PostgreSQL/pgvector para recuperación contextual de información.",
        "La búsqueda semántica funciona convirtiendo las consultas en vectores de 384 dimensiones usando el modelo paraphrase-multilingual-MiniLM-L12-v2, que luego se comparan con vectores almacenados en la base de datos mediante similitud coseno.",
        "El sistema utiliza PostgreSQL con la extensión pgvector para almacenar y buscar embeddings vectoriales de manera eficiente.",
        "El tiempo de respuesta objetivo es menor a 500 milisegundos para búsquedas básicas, con tiempos aceptables hasta 2s para queries complejas.",
        "Los documentos PDF se procesan extrayendo texto con PyPDF2, luego se dividen en chunks y se generan embeddings para cada fragmento usando sentence-transformers.",
        "El sistema utiliza sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, un modelo especializado en embeddings semánticos con soporte multilingüe y 384 dimensiones.",
        "El sistema puede manejar hasta 50 usuarios concurrentes con un throughput de 45.6 requests por segundo según las pruebas de capacidad.",
        "El API expone endpoints como /search para búsqueda semántica, /upload para subir documentos, /health para verificar el estado del servicio.",
    ],
    "contexts": [
        # Contextos recuperados por el sistema RAG (documentos relevantes)
        ["Es un sistema de Retrieval Augmented Generation que combina búsqueda semántica en documentos con generación de respuestas contextualizadas usando PostgreSQL con pgvector. Permite consultar documentos técnicos y obtener respuestas precisas basadas en el contenido almacenado."],
        ["El sistema convierte consultas de texto en vectores numéricos usando modelos de embeddings pre-entrenados. Estos vectores se comparan con los vectores de documentos almacenados en la base de datos usando similitud coseno. Los documentos más similares se recuperan y se usan como contexto para generar respuestas."],
        ["PostgreSQL 14+ con la extensión pgvector instalada. Esta extensión permite almacenar y buscar eficientemente vectores de alta dimensionalidad usando índices IVFFlat o HNSW."],
        ["El sistema está diseñado para responder en menos de 500ms para consultas simples y menos de 2 segundos para consultas complejas que requieren múltiples búsquedas. El tiempo incluye vectorización, búsqueda en BD y generación de respuesta."],
        ["Los PDFs se procesan extrayendo primero el texto usando librerías como PyPDF2 o pypdf. Luego el texto se divide en chunks de ~500 tokens. Cada chunk se convierte en un embedding usando el modelo sentence-transformers y se almacena en PostgreSQL con su metadata."],
        ["Se utiliza el modelo paraphrase-multilingual-MiniLM-L12-v2 de Sentence Transformers, que genera embeddings de 384 dimensiones optimizados para búsqueda semántica multilingüe. Este modelo fue entrenado en más de 50 idiomas incluyendo español e inglés."],
        ["Según las pruebas de carga realizadas con Locust, el sistema maneja eficientemente hasta 50 usuarios concurrentes con un throughput promedio de 45.6 requests/segundo. El tiempo de respuesta promedio se mantiene en 527 microsegundos bajo carga."],
        ["El API REST expone: /search (POST) para búsqueda semántica, /upload (POST) para subir documentos PDF, /health (GET) para health check, /documents (GET) para listar documentos, /documents/{id} (DELETE) para eliminar documentos."],
    ],
    "ground_truth": [
        # Respuestas de referencia (ground truth) para comparación
        "Es un sistema de Retrieval Augmented Generation que combina búsqueda semántica en documentos con generación de respuestas contextualizadas usando PostgreSQL con pgvector.",
        "El sistema convierte consultas en vectores usando modelos de embeddings y los compara con vectores de documentos almacenados mediante similitud coseno.",
        "PostgreSQL 14+ con la extensión pgvector para almacenar y buscar vectores eficientemente.",
        "El sistema está diseñado para responder en menos de 500ms para consultas simples y menos de 2 segundos para consultas complejas.",
        "Los PDFs se procesan extrayendo texto, dividiendo en chunks, generando embeddings y almacenando en PostgreSQL con metadata.",
        "Se utiliza el modelo paraphrase-multilingual-MiniLM-L12-v2 de Sentence Transformers, que genera embeddings de 384 dimensiones optimizados para búsqueda semántica multilingüe.",
        "El sistema maneja hasta 50 usuarios concurrentes con un throughput de 45.6 requests/segundo según pruebas con Locust.",
        "El API expone /search (búsqueda semántica), /upload (subir PDFs), /health (verificación), /documents (listar) y /documents/{id} (eliminar).",
    ]
}

# =============================================================================
# FUNCIONES DE EVALUACIÓN
# =============================================================================

def crear_dataset_ragas():
    """Crea un dataset en formato RAGAS desde el diccionario."""
    dataset = Dataset.from_dict(RAGAS_DATASET)
    print(f"✅ Dataset creado con {len(dataset)} casos")
    return dataset


def evaluar_con_ragas(dataset, metricas=None):
    """
    Evalúa el sistema RAG usando RAGAS con OpenAI.
    
    Args:
        dataset: Dataset de RAGAS con question, answer, contexts, ground_truth
        metricas: Lista de métricas a evaluar. Si es None, usa todas.
    
    Returns:
        Resultado de la evaluación con scores por métrica
    """
    if metricas is None:
        # Métricas por defecto (todas las disponibles)
        metricas = [
            faithfulness,           # ¿Respuesta fiel al contexto?
            answer_relevancy,       # ¿Respuesta relevante a la pregunta?
            context_precision,      # ¿Contexto recuperado es preciso?
            context_recall,         # ¿Contexto recuperado es completo?
            answer_similarity,      # Similitud semántica (SemScore)
            answer_correctness,     # Corrección general
        ]
    
    print("\n🔍 Evaluando con RAGAS + OpenAI...")
    print(f"Métricas: {[m.name for m in metricas]}")
    print(f"Modelo LLM: {llm.model_name}")
    print(f"Costo estimado: ~$0.10-0.30 USD para 8 casos\n")
    
    # Ejecutar evaluación
    resultado = evaluate(
        dataset,
        metrics=metricas,
        llm=llm,
        embeddings=embeddings,
    )
    
    return resultado


def generar_reporte_ragas(resultado, ruta_salida="reports/ragas_evaluation.txt"):
    """
    Genera un reporte detallado de los resultados de RAGAS.
    
    Args:
        resultado: Resultado de evaluate()
        ruta_salida: Ruta donde guardar el reporte
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    
    # Convertir a DataFrame para análisis
    df = resultado.to_pandas()
    
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("EVALUACIÓN RAG CON RAGAS FRAMEWORK\n")
        f.write("="*80 + "\n\n")
        f.write(f"Fecha: {datetime.now().strftime('%d de %B, %Y - %H:%M:%S')}\n")
        f.write(f"Total de casos evaluados: {len(df)}\n\n")
        
        # Métricas agregadas
        f.write("MÉTRICAS PROMEDIO:\n")
        f.write("-"*80 + "\n")
        
        # Extraer métricas numéricas
        metricas_columnas = [col for col in df.columns if col not in ['question', 'answer', 'contexts', 'ground_truth']]
        
        for metrica in metricas_columnas:
            if df[metrica].dtype in ['float64', 'int64']:
                promedio = df[metrica].mean()
                std = df[metrica].std()
                f.write(f"  {metrica:25s}: {promedio:.4f} ± {std:.4f}\n")
        
        f.write("\n")
        
        # Interpretación de métricas
        f.write("INTERPRETACIÓN DE MÉTRICAS:\n")
        f.write("-"*80 + "\n")
        f.write("  faithfulness        : Qué tan fiel es la respuesta al contexto (0-1)\n")
        f.write("                        > 0.7 = Buena, < 0.5 = Revisa alucinaciones\n")
        f.write("  answer_relevancy    : Qué tan relevante es la respuesta (0-1)\n")
        f.write("                        > 0.7 = Buena, < 0.5 = Respuestas off-topic\n")
        f.write("  context_precision   : Precisión del contexto recuperado (0-1)\n")
        f.write("                        > 0.7 = Buen retrieval, < 0.5 = Ruido\n")
        f.write("  context_recall      : Completitud del contexto (0-1)\n")
        f.write("                        > 0.7 = Completo, < 0.5 = Falta información\n")
        f.write("  answer_similarity   : Similitud semántica con ground truth (0-1)\n")
        f.write("                        > 0.7 = Alta similitud, < 0.5 = Muy diferente\n")
        f.write("  answer_correctness  : Corrección general (0-1)\n")
        f.write("                        > 0.7 = Correcta, < 0.5 = Incorrecta\n")
        f.write("\n")
        
        # Resultados por caso
        f.write("RESULTADOS POR CASO:\n")
        f.write("-"*80 + "\n\n")
        
        for idx, row in df.iterrows():
            f.write(f"Caso {idx+1}:\n")
            for metrica in metricas_columnas:
                if metrica in row and pd.notna(row[metrica]):
                    if isinstance(row[metrica], (int, float)):
                        valor = row[metrica]
                        # Interpretación cualitativa
                        if valor >= 0.8:
                            nivel = "EXCELENTE"
                        elif valor >= 0.7:
                            nivel = "BUENA"
                        elif valor >= 0.5:
                            nivel = "ACEPTABLE"
                        else:
                            nivel = "REVISAR"
                        f.write(f"  {metrica:25s}: {valor:.4f}  [{nivel}]\n")
            f.write("\n")
        
        # Análisis de fortalezas y debilidades
        f.write("ANÁLISIS:\n")
        f.write("-"*80 + "\n")
        
        for metrica in metricas_columnas:
            if df[metrica].dtype in ['float64', 'int64']:
                promedio = df[metrica].mean()
                if promedio >= 0.8:
                    f.write(f"✅ {metrica}: EXCELENTE ({promedio:.3f})\n")
                elif promedio >= 0.7:
                    f.write(f"✅ {metrica}: BUENA ({promedio:.3f})\n")
                elif promedio >= 0.5:
                    f.write(f"⚠️  {metrica}: ACEPTABLE ({promedio:.3f}) - Revisar casos individuales\n")
                else:
                    f.write(f"❌ {metrica}: NECESITA MEJORA ({promedio:.3f}) - Acción requerida\n")
        
        f.write("\n")
        f.write("="*80 + "\n")
    
    print(f"\n✅ Reporte guardado en: {ruta_salida}")
    return df


def imprimir_resumen(resultado):
    """Imprime un resumen rápido de los resultados."""
    df = resultado.to_pandas()
    
    print("\n" + "="*80)
    print("📊 RESUMEN DE EVALUACIÓN RAGAS")
    print("="*80)
    
    metricas_columnas = [col for col in df.columns if col not in ['question', 'answer', 'contexts', 'ground_truth']]
    
    for metrica in metricas_columnas:
        if df[metrica].dtype in ['float64', 'int64']:
            promedio = df[metrica].mean()
            if promedio >= 0.7:
                emoji = "✅"
            elif promedio >= 0.5:
                emoji = "⚠️"
            else:
                emoji = "❌"
            print(f"{emoji} {metrica:25s}: {promedio:.4f}")
    
    print("="*80)


# =============================================================================
# TESTS CON PYTEST
# =============================================================================

def test_ragas_evaluacion_completa():
    """Test principal: evalúa con todas las métricas RAGAS."""
    # Crear dataset
    dataset = crear_dataset_ragas()
    
    # Evaluar
    resultado = evaluar_con_ragas(dataset)
    
    # Generar reporte
    df = generar_reporte_ragas(resultado)
    
    # Imprimir resumen
    imprimir_resumen(resultado)
    
    # Aserciones: verificar que las métricas estén en rangos aceptables
    assert df['faithfulness'].mean() > 0.5, "Faithfulness muy baja - posibles alucinaciones"
    assert df['answer_relevancy'].mean() > 0.5, "Answer Relevancy baja - respuestas no relevantes"
    
    print("\n✅ Evaluación RAGAS completada exitosamente")


def test_ragas_faithfulness():
    """Test: evalúa solo Faithfulness (fidelidad al contexto)."""
    dataset = crear_dataset_ragas()
    
    resultado = evaluar_con_ragas(dataset, metricas=[faithfulness])
    df = resultado.to_pandas()
    
    promedio = df['faithfulness'].mean()
    print(f"\n📊 Faithfulness promedio: {promedio:.4f}")
    
    if promedio >= 0.8:
        print("✅ EXCELENTE: Respuestas muy fieles al contexto")
    elif promedio >= 0.7:
        print("✅ BUENA: Respuestas generalmente fieles")
    elif promedio >= 0.5:
        print("⚠️ ACEPTABLE: Algunas inconsistencias")
    else:
        print("❌ REVISAR: Posibles alucinaciones frecuentes")
    
    assert promedio > 0.5, f"Faithfulness muy baja: {promedio:.4f}"


def test_ragas_answer_relevancy():
    """Test: evalúa solo Answer Relevancy (relevancia de respuesta)."""
    dataset = crear_dataset_ragas()
    
    resultado = evaluar_con_ragas(dataset, metricas=[answer_relevancy])
    df = resultado.to_pandas()
    
    promedio = df['answer_relevancy'].mean()
    print(f"\n📊 Answer Relevancy promedio: {promedio:.4f}")
    
    if promedio >= 0.8:
        print("✅ EXCELENTE: Respuestas muy relevantes")
    elif promedio >= 0.7:
        print("✅ BUENA: Respuestas generalmente relevantes")
    elif promedio >= 0.5:
        print("⚠️ ACEPTABLE: Algunas respuestas off-topic")
    else:
        print("❌ REVISAR: Respuestas frecuentemente irrelevantes")
    
    assert promedio > 0.5, f"Answer Relevancy muy baja: {promedio:.4f}"


def test_ragas_context_precision():
    """Test: evalúa Context Precision (precisión del retrieval)."""
    dataset = crear_dataset_ragas()
    
    resultado = evaluar_con_ragas(dataset, metricas=[context_precision])
    df = resultado.to_pandas()
    
    promedio = df['context_precision'].mean()
    print(f"\n📊 Context Precision promedio: {promedio:.4f}")
    
    if promedio >= 0.8:
        print("✅ EXCELENTE: Retrieval muy preciso")
    elif promedio >= 0.7:
        print("✅ BUENA: Retrieval generalmente preciso")
    elif promedio >= 0.5:
        print("⚠️ ACEPTABLE: Algo de ruido en resultados")
    else:
        print("❌ REVISAR: Demasiado ruido en retrieval")
    
    assert promedio > 0.4, f"Context Precision muy baja: {promedio:.4f}"


def test_ragas_answer_similarity():
    """Test: evalúa Answer Similarity (SemScore de Hugging Face)."""
    dataset = crear_dataset_ragas()
    
    resultado = evaluar_con_ragas(dataset, metricas=[answer_similarity])
    df = resultado.to_pandas()
    
    promedio = df['answer_similarity'].mean()
    print(f"\n📊 Answer Similarity (SemScore) promedio: {promedio:.4f}")
    
    if promedio >= 0.8:
        print("✅ EXCELENTE: Alta similitud semántica")
    elif promedio >= 0.7:
        print("✅ BUENA: Buena similitud semántica")
    elif promedio >= 0.5:
        print("⚠️ ACEPTABLE: Similitud moderada")
    else:
        print("❌ REVISAR: Similitud baja")
    
    # SemScore es similar a BERT Score que ya implementamos
    # Comparar con nuestro BERT Score previo: 0.8335
    print(f"\n💡 Comparación: BERT Score previo = 0.8335")
    
    assert promedio > 0.5, f"Answer Similarity muy baja: {promedio:.4f}"


# =============================================================================
# SCRIPT PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    print("🚀 Iniciando evaluación RAGAS del sistema Aconex RAG")
    print("="*80)
    
    # Verificar API key de OpenAI
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY no configurada")
        print("\nPor favor configura tu API key de OpenAI:")
        print("  PowerShell: $env:OPENAI_API_KEY='sk-proj-tu-key-aqui'")
        print("  Bash: export OPENAI_API_KEY='sk-proj-tu-key-aqui'")
        print("  o crea un archivo .env con: OPENAI_API_KEY=sk-proj-...")
        print("\n💡 Obtener API key (incluye $5 gratis):")
        print("   https://platform.openai.com/api-keys")
        print("\n💰 Costo estimado para esta prueba: $0.10-0.30 USD (8 casos)")
        exit(1)
    
    print("✅ API key de OpenAI configurada")
    print(f"🤖 Usando modelo: {llm.model_name}")
    print(f"💰 Costo estimado: ~$0.10-0.30 USD\n")
    
    # Crear dataset
    dataset = crear_dataset_ragas()
    
    # Evaluar con todas las métricas
    resultado = evaluar_con_ragas(dataset)
    
    # Generar reporte
    df = generar_reporte_ragas(resultado)
    
    # Imprimir resumen
    imprimir_resumen(resultado)
    
    # Guardar también como CSV para análisis
    df.to_csv("reports/ragas_results.csv", index=False, encoding='utf-8')
    print(f"\n✅ Resultados también guardados en: reports/ragas_results.csv")
    
    print("\n🎉 Evaluación completada!")
