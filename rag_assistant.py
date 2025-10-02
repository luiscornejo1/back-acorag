#!/usr/bin/env python3
"""
Sistema RAG con respuesta conversacional
Combina búsqueda semántica + generación de respuesta con contexto
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
from app.search_core import semantic_search
from app.utils import get_db_connection

load_dotenv()

app = FastAPI(title="Aconex RAG Assistant", version="1.0")

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
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Contar documentos totales
        cur.execute("SELECT COUNT(DISTINCT document_id) FROM chunks")
        total_docs = cur.fetchone()[0]
        
        # Contar chunks totales
        cur.execute("SELECT COUNT(*) FROM chunks")
        total_chunks = cur.fetchone()[0]
        
        # Análisis por categorías
        cur.execute("""
            SELECT category, COUNT(DISTINCT document_id) as doc_count, COUNT(*) as chunk_count
            FROM chunks 
            WHERE category IS NOT NULL 
            GROUP BY category 
            ORDER BY doc_count DESC
        """)
        categories = cur.fetchall()
        
        # Análisis por tipos de documento
        cur.execute("""
            SELECT doc_type, COUNT(DISTINCT document_id) as doc_count
            FROM chunks 
            WHERE doc_type IS NOT NULL 
            GROUP BY doc_type 
            ORDER BY doc_count DESC
        """)
        doc_types = cur.fetchall()
        
        # Proyectos únicos
        cur.execute("""
            SELECT project_id, COUNT(DISTINCT document_id) as doc_count
            FROM chunks 
            WHERE project_id IS NOT NULL 
            GROUP BY project_id
        """)
        projects = cur.fetchall()
        
        # Documentos más recientes
        cur.execute("""
            SELECT title, date_modified 
            FROM chunks 
            WHERE date_modified IS NOT NULL 
            ORDER BY date_modified DESC 
            LIMIT 5
        """)
        recent_docs = cur.fetchall()
        
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
        return {"error": str(e)}

def detect_question_type(question: str) -> str:
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
        
        response = f"## 📊 Estadísticas del Sistema\n\n"
        response += f"**Total de documentos únicos:** {stats['total_documents']:,}\n"
        response += f"**Total de fragmentos indexados:** {stats['total_chunks']:,}\n\n"
        
        if stats['categories']:
            response += "**Documentos por categoría:**\n"
            for cat, doc_count, chunk_count in stats['categories'][:5]:
                response += f"• {cat}: {doc_count:,} documentos ({chunk_count:,} fragmentos)\n"
        
        if stats['projects']:
            response += "\n**Proyectos activos:**\n"
            for proj, doc_count in stats['projects']:
                response += f"• {proj}: {doc_count:,} documentos\n"
        
        return response
    
    elif question_type == "types":
        stats = analyze_database_stats()
        if "error" in stats:
            return "Error al acceder a los tipos de documentos."
        
        response = f"## 📋 Tipos de Documentos Disponibles\n\n"
        if stats['document_types']:
            response += "**Clasificación por tipo:**\n"
            for doc_type, count in stats['document_types']:
                response += f"• **{doc_type}**: {count:,} documentos\n"
        
        if stats['categories']:
            response += "\n**Categorías disponibles:**\n"
            for cat, doc_count, _ in stats['categories']:
                response += f"• {cat}: {doc_count:,} documentos\n"
        
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
        "message": "Aconex RAG Assistant",
        "version": "1.0",
        "endpoints": {
            "chat": "/chat - Búsqueda conversacional",
            "search": "/search - Búsqueda tradicional",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok", "message": "Asistente RAG funcionando"}

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
    Búsqueda conversacional que devuelve respuesta con contexto
    """
    try:
        print(f"🤖 Pregunta: '{req.question}'")
        
        # 1. Realizar búsqueda semántica
        project_id = req.project_id if req.project_id != "string" else None
        
        search_results = semantic_search(
            query=req.question,
            project_id=project_id,
            top_k=req.max_context_docs,
            probes=10
        )
        
        print(f"📊 Documentos encontrados: {len(search_results)}")
        
        # 2. Generar respuesta contextual
        response_text = generate_context_response(req.question, search_results)
        
        # 3. Devolver respuesta + documentos de referencia
        return {
            "question": req.question,
            "answer": response_text,
            "sources": search_results,
            "source_count": len(search_results),
            "project_id": project_id
        }
        
    except Exception as e:
        return {
            "question": req.question,
            "answer": f"Error procesando la pregunta: {str(e)}",
            "sources": [],
            "source_count": 0
        }

if __name__ == "__main__":
    import uvicorn
    print("🤖 Iniciando Asistente RAG en http://localhost:8000")
    print("📚 Endpoints:")
    print("   POST /chat - Búsqueda conversacional")
    print("   POST /search - Búsqueda tradicional")
    print("   GET  /docs - Documentación")
    uvicorn.run(app, host="0.0.0.0", port=8000)