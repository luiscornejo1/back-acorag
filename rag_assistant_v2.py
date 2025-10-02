#!/usr/bin/env python3
"""
Sistema RAG con respuesta conversacional inteligente
Combina búsqueda semántica + análisis de datos + generación de respuesta con        response = f        response = f"## � Tipos de Documentos Disponibles\n\n"
        if stats['document_types']:
            response += "**Clasificación por tipo:**\n"
            for doc_type, count in stats['document_types']:
                if doc_type:  # Solo mostrar si el tipo no es None
                    response += f"• **{doc_type}**: {count:,} documentos\n"
        else:
            response += "**Sin tipos de documentos definidos**\n"
        
        if stats['categories']:
            response += "\n**Categorías disponibles:**\n"
            for cat, doc_count, _ in stats['categories']:
                response += f"• {cat}: {doc_count:,} documentos\n"adísticas del Sistema\n\n"
        response += f"**Total de documentos únicos:** {stats['total_documents']:,}\n"
        response += f"**Total de fragmentos indexados:** {stats['total_chunks']:,}\n\n"
        
        if stats['categories']:
            response += "**Documentos por categoría:**\n"
            for cat, doc_count, chunk_count in stats['categories'][:5]:
                if cat:  # Solo mostrar si la categoría no es None
                    response += f"• {cat}: {doc_count:,} documentos ({chunk_count:,} fragmentos)\n"
        else:
            response += "**Sin categorías definidas en los documentos**\n"
"""
import os
import json
import re
from collections import Counter, defaultdict
from typing import List, Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import psycopg2
import logging

# Importar funciones existentes
import sys
sys.path.append(os.path.dirname(__file__))
from app.search_core import semantic_search, get_conn

load_dotenv()

app = FastAPI(title="Aconex RAG Assistant", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str
    project_id: str = None
    max_context_docs: int = 10  # Aumentado para mejor análisis

class SearchRequest(BaseModel):
    query: str
    project_id: str = None
    top_k: int = 5
    probes: int = 10

def analyze_database_stats() -> Dict[str, Any]:
    """
    Analiza estadísticas completas de la base de datos
    """
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Contar documentos totales
        cur.execute("SELECT COUNT(DISTINCT document_id) FROM document_chunks")
        total_docs = cur.fetchone()[0]
        
        # Contar chunks totales
        cur.execute("SELECT COUNT(*) FROM document_chunks")
        total_chunks = cur.fetchone()[0]

        # Análisis por proyectos (más simple y seguro)
        try:
            cur.execute("""
                SELECT dc.project_id, COUNT(DISTINCT dc.document_id) as doc_count, COUNT(*) as chunk_count
                FROM document_chunks dc
                WHERE dc.project_id IS NOT NULL 
                GROUP BY dc.project_id 
                ORDER BY doc_count DESC
            """)
            categories = cur.fetchall()  # Usamos como "categorías" los proyectos
        except Exception as e:
            print(f"Error obteniendo proyectos: {e}")
            categories = []

        # Análisis básico por títulos (simulando tipos)
        try:
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN LOWER(dc.title) LIKE '%informe%' THEN 'Informes'
                        WHEN LOWER(dc.title) LIKE '%calidad%' THEN 'Control de Calidad'
                        WHEN LOWER(dc.title) LIKE '%reporte%' THEN 'Reportes'
                        WHEN LOWER(dc.title) LIKE '%plan%' THEN 'Planes'
                        ELSE 'Otros'
                    END as doc_type,
                    COUNT(DISTINCT dc.document_id) as doc_count
                FROM document_chunks dc
                WHERE dc.title IS NOT NULL 
                GROUP BY doc_type 
                ORDER BY doc_count DESC
            """)
            doc_types = cur.fetchall()
        except Exception as e:
            print(f"Error obteniendo tipos: {e}")
            doc_types = []
        
        # Proyectos únicos
        try:
            cur.execute("""
                SELECT dc.project_id, COUNT(DISTINCT dc.document_id) as doc_count
                FROM document_chunks dc
                WHERE dc.project_id IS NOT NULL 
                GROUP BY dc.project_id
            """)
            projects = cur.fetchall()
        except Exception as e:
            print(f"Error obteniendo proyectos únicos: {e}")
            projects = []
        
        # Documentos más recientes
        try:
            cur.execute("""
                SELECT dc.title, MAX(dc.date_modified) as latest_date
                FROM document_chunks dc
                WHERE dc.date_modified IS NOT NULL 
                GROUP BY dc.title, dc.document_id
                ORDER BY latest_date DESC 
                LIMIT 5
            """)
            recent_docs = cur.fetchall()
        except Exception as e:
            print(f"Error obteniendo documentos recientes: {e}")
            recent_docs = []
        
        cur.close()
        conn.close()
        
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "categories": categories,
            "document_types": doc_types,
            "projects": projects,
            "recent_documents": recent_docs
        }
        
    except Exception as e:
        logging.error(f"Error analyzing database: {e}")
        return {"error": str(e)}def detect_question_type(question: str) -> str:
    """
    Detecta el tipo de pregunta para generar respuesta apropiada
    """
    question_lower = question.lower()
    
    # Preguntas sobre cantidad/estadísticas
    if any(word in question_lower for word in ['cuántos', 'cuantos', 'cantidad', 'total', 'número', 'estadísticas']):
        return "statistics"
    
    # Preguntas sobre tipos
    if any(word in question_lower for word in ['qué tipos', 'que tipos', 'categorías', 'categorias', 'clasificación']):
        return "types"
    
    # Preguntas sobre proyectos
    if any(word in question_lower for word in ['proyecto', 'proyectos']):
        return "projects"
    
    # Preguntas sobre documentos recientes
    if any(word in question_lower for word in ['reciente', 'recientes', 'último', 'últimos', 'nuevo', 'nuevos']):
        return "recent"
    
    # Búsqueda específica de contenido
    return "content_search"

def generate_intelligent_response(question: str, relevant_docs: List[Dict], question_type: str) -> str:
    """
    Genera respuesta inteligente basada en el tipo de pregunta y análisis real de datos
    """
    
    if question_type == "statistics":
        stats = analyze_database_stats()
        if "error" in stats:
            return "Error al acceder a las estadísticas de la base de datos."
        
        response = f"## � Estadísticas del Sistema de Emails\n\n"
        response += f"**Total de emails únicos:** {stats['total_documents']:,}\n"
        response += f"**Total de fragmentos indexados:** {stats['total_chunks']:,}\n\n"
        
        if stats['categories']:
            response += "**Emails por proyecto:**\n"
            for cat, doc_count, chunk_count in stats['categories'][:5]:
                response += f"• {cat}: {doc_count:,} emails ({chunk_count:,} fragmentos)\n"
        
        if stats['projects']:
            response += "\n**Proyectos activos:**\n"
            for proj, doc_count in stats['projects']:
                response += f"• {proj}: {doc_count:,} documentos\n"
        
        return response
    
    elif question_type == "types":
        stats = analyze_database_stats()
        if "error" in stats:
            return "Error al acceder a los tipos de documentos."
        
        response = f"## � Tipos de Emails Disponibles\n\n"
        if stats['document_types']:
            response += "**Clasificación por asunto:**\n"
            for doc_type, count in stats['document_types']:
                response += f"• **{doc_type}**: {count:,} emails\n"
        
        if stats['categories']:
            response += "\n**Proyectos disponibles:**\n"
            for cat, doc_count, _ in stats['categories']:
                response += f"• {cat}: {doc_count:,} emails\n"
        
        return response
    
    elif question_type == "projects":
        stats = analyze_database_stats()
        if "error" in stats:
            return "Error al acceder a la información de proyectos."
        
        response = f"## 🏗️ Información de Proyectos\n\n"
        if stats['projects']:
            response += "**Proyectos en el sistema:**\n"
            for proj, doc_count in stats['projects']:
                response += f"• **{proj}**: {doc_count:,} documentos\n"
        
        # Buscar documentos relacionados con la pregunta
        if relevant_docs:
            response += f"\n**Documentos relevantes encontrados:** {len(relevant_docs)}\n"
            for i, doc in enumerate(relevant_docs[:3], 1):
                title = doc.get('title', 'Sin título')[:80]
                score = doc.get('score', 0)
                response += f"{i}. **{title}** (Relevancia: {score:.2f})\n"
        
        return response
    
    elif question_type == "recent":
        stats = analyze_database_stats()
        if "error" in stats:
            return "Error al acceder a documentos recientes."
        
        response = f"## 🕒 Documentos Recientes\n\n"
        if stats['recent_documents']:
            response += "**Documentos modificados recientemente:**\n"
            for title, date_mod in stats['recent_documents']:
                date_str = date_mod.strftime("%Y-%m-%d") if date_mod else "Sin fecha"
                response += f"• **{title[:60]}...** ({date_str})\n"
        
        return response
    
    else:  # content_search
        if not relevant_docs:
            return f"No encontré información específica sobre '{question}' en los documentos disponibles. Intenta reformular tu pregunta o usar términos más específicos."
        
        # Análisis más detallado del contenido
        response = f"## 🔍 Resultados para: {question}\n\n"
        response += f"**Encontré {len(relevant_docs)} documentos relevantes**\n\n"
        
        # Agrupar por proyectos/categorías
        by_category = defaultdict(list)
        by_project = defaultdict(list)
        
        for doc in relevant_docs:
            cat = doc.get('category', 'Sin categoría')
            proj = doc.get('project_id', 'Sin proyecto')
            by_category[cat].append(doc)
            by_project[proj].append(doc)
        
        if len(by_category) > 1:
            response += "**Por categoría:**\n"
            for cat, docs in by_category.items():
                response += f"• {cat}: {len(docs)} documentos\n"
            response += "\n"
        
        response += "**Documentos más relevantes:**\n"
        for i, doc in enumerate(relevant_docs[:5], 1):
            score = doc.get('score', 0)
            title = doc.get('title', 'Sin título')[:70]
            snippet = doc.get('snippet', '')[:150]
            response += f"{i}. **{title}** (Relevancia: {score:.2f})\n"
            if snippet:
                response += f"   _{snippet}_...\n\n"
        
        if len(relevant_docs) > 5:
            response += f"\n💡 Hay {len(relevant_docs)-5} documentos adicionales relacionados.\n"
        
        return response

@app.get("/")
def root():
    return {
        "message": "Aconex RAG Assistant v2.0",
        "version": "2.0",
        "features": [
            "Análisis inteligente de preguntas",
            "Estadísticas en tiempo real",
            "Búsqueda semántica avanzada",
            "Respuestas contextuales"
        ],
        "endpoints": {
            "chat": "/chat - Búsqueda conversacional inteligente",
            "search": "/search - Búsqueda semántica tradicional",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok", "message": "Asistente RAG v2.0 funcionando"}

@app.post("/search")
def search(req: SearchRequest) -> List[Dict[str, Any]]:
    """Búsqueda semántica tradicional"""
    try:
        project_id = req.project_id if req.project_id != "string" else None
        
        results = semantic_search(
            query=req.query,
            project_id=project_id,
            top_k=req.top_k,
            probes=req.probes
        )
        
        return results
        
    except Exception as e:
        return [{"error": str(e)}]

@app.post("/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:
    """
    Búsqueda conversacional inteligente que analiza la pregunta y genera respuesta apropiada
    """
    try:
        print(f"🤖 Pregunta: '{req.question}'")
        
        # 1. Detectar tipo de pregunta
        question_type = detect_question_type(req.question)
        print(f"📋 Tipo detectado: {question_type}")
        
        # 2. Realizar búsqueda semántica (siempre, para contexto)
        project_id = req.project_id if req.project_id != "string" else None
        
        # Para preguntas estadísticas, buscar más documentos
        search_limit = req.max_context_docs if question_type == "content_search" else min(req.max_context_docs * 2, 20)
        
        results = semantic_search(
            query=req.question,
            project_id=project_id,
            top_k=search_limit,
            probes=20  # Aumentar precisión
        )
        
        print(f"🔍 Encontrados: {len(results)} resultados")
        
        # 3. Generar respuesta inteligente
        answer = generate_intelligent_response(req.question, results, question_type)
        
        # 4. Preparar contexto para mostrar fuentes
        context_docs = results[:req.max_context_docs]  # Limitar fuentes mostradas
        
        return {
            "question": req.question,
            "answer": answer,
            "sources": context_docs,
            "question_type": question_type,
            "total_found": len(results),
            "context_used": f"Se analizaron {len(results)} documentos para generar esta respuesta."
        }
        
    except Exception as e:
        print(f"❌ Error en chat: {e}")
        return {
            "question": req.question,
            "answer": f"Error procesando la pregunta: {str(e)}",
            "sources": [],
            "context_used": "Error en el procesamiento"
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Aconex RAG Assistant v2.0...")
    uvicorn.run(app, host="0.0.0.0", port=8000)