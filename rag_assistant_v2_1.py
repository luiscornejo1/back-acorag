#!/usr/bin/env python3
"""
Sistema RAG con respuesta conversacional inteligente v2.1
Versión simplificada que evita errores de columnas
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

app = FastAPI(title="Aconex RAG Assistant", version="2.1")

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
    max_context_docs: int = 20

class SearchRequest(BaseModel):
    query: str
    project_id: str = None
    top_k: int = 20
    probes: int = 10

class QueryRequest(BaseModel):
    template_name: str = None
    custom_query: str = None
    parameters: Dict[str, Any] = {}

def execute_safe_query(query: str, params: tuple = None) -> Dict[str, Any]:
    """
    Ejecuta una consulta SQL de forma segura y retorna resultados formateados
    """
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        
        # Obtener nombres de columnas
        columns = [desc[0] for desc in cur.description]
        
        # Convertir resultados a lista de diccionarios
        results = []
        for row in cur.fetchall():
            results.append(dict(zip(columns, row)))
        
        cur.close()
        conn.close()
        
        return {"success": True, "data": results, "query": query}
        
    except Exception as e:
        return {"error": str(e), "query": query}

def analyze_database_stats() -> Dict[str, Any]:
    """
    Analiza estadísticas de la base de datos usando solo document_chunks
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

        # Análisis por proyectos
        cur.execute("""
            SELECT project_id, COUNT(DISTINCT document_id) as doc_count, COUNT(*) as chunk_count
            FROM document_chunks
            WHERE project_id IS NOT NULL 
            GROUP BY project_id 
            ORDER BY doc_count DESC
        """)
        categories = cur.fetchall()

        # Análisis por tipos (basado en títulos)
        cur.execute("""
            SELECT 
                CASE 
                    WHEN LOWER(title) LIKE '%informe%' THEN 'Informes'
                    WHEN LOWER(title) LIKE '%calidad%' THEN 'Control de Calidad'
                    WHEN LOWER(title) LIKE '%reporte%' THEN 'Reportes'
                    WHEN LOWER(title) LIKE '%plan%' THEN 'Planes'
                    WHEN LOWER(title) LIKE '%procedimiento%' THEN 'Procedimientos'
                    ELSE 'Otros'
                END as doc_type,
                COUNT(DISTINCT document_id) as doc_count
            FROM document_chunks
            WHERE title IS NOT NULL 
            GROUP BY doc_type 
            ORDER BY doc_count DESC
        """)
        doc_types = cur.fetchall()
        
        # Proyectos únicos
        cur.execute("""
            SELECT project_id, COUNT(DISTINCT document_id) as doc_count
            FROM document_chunks
            WHERE project_id IS NOT NULL 
            GROUP BY project_id
        """)
        projects = cur.fetchall()
        
        # Documentos más recientes
        cur.execute("""
            SELECT title, MAX(date_modified) as latest_date
            FROM document_chunks
            WHERE date_modified IS NOT NULL 
            GROUP BY title, document_id
            ORDER BY latest_date DESC 
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

def analyze_file_types() -> Dict[str, Any]:
    """
    Analiza específicamente los tipos de archivos (PDF, Word, Excel) en la base de datos
    """
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Análisis por extensión de archivo basado en filename de la tabla documents
        cur.execute("""
            SELECT 
                CASE 
                    WHEN LOWER(d.filename) LIKE '%.pdf' THEN 'PDF'
                    WHEN LOWER(d.filename) LIKE '%.doc%' THEN 'Word'
                    WHEN LOWER(d.filename) LIKE '%.xls%' THEN 'Excel'
                    WHEN LOWER(d.filename) LIKE '%.ppt%' THEN 'PowerPoint'
                    WHEN LOWER(d.filename) LIKE '%.txt' THEN 'Texto'
                    WHEN LOWER(d.filename) LIKE '%.csv' THEN 'CSV'
                    ELSE 'Otro'
                END as file_type,
                COUNT(DISTINCT dc.document_id) as doc_count,
                COUNT(*) as chunk_count
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.document_id
            WHERE d.filename IS NOT NULL 
            GROUP BY 
                CASE 
                    WHEN LOWER(d.filename) LIKE '%.pdf' THEN 'PDF'
                    WHEN LOWER(d.filename) LIKE '%.doc%' THEN 'Word'
                    WHEN LOWER(d.filename) LIKE '%.xls%' THEN 'Excel'
                    WHEN LOWER(d.filename) LIKE '%.ppt%' THEN 'PowerPoint'
                    WHEN LOWER(d.filename) LIKE '%.txt' THEN 'Texto'
                    WHEN LOWER(d.filename) LIKE '%.csv' THEN 'CSV'
                    ELSE 'Otro'
                END
            ORDER BY doc_count DESC
        """)
        file_types = cur.fetchall()
        
        # Análisis detallado de PDFs por proyecto
        cur.execute("""
            SELECT dc.project_id, COUNT(DISTINCT dc.document_id) as pdf_count
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.document_id
            WHERE LOWER(d.filename) LIKE '%.pdf' AND dc.project_id IS NOT NULL
            GROUP BY dc.project_id
            ORDER BY pdf_count DESC
        """)
        pdf_by_project = cur.fetchall()
        
        # Análisis detallado de Word por proyecto
        cur.execute("""
            SELECT dc.project_id, COUNT(DISTINCT dc.document_id) as word_count
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.document_id
            WHERE LOWER(d.filename) LIKE '%.doc%' AND dc.project_id IS NOT NULL
            GROUP BY dc.project_id
            ORDER BY word_count DESC
        """)
        word_by_project = cur.fetchall()
        
        # Análisis detallado de Excel por proyecto
        cur.execute("""
            SELECT dc.project_id, COUNT(DISTINCT dc.document_id) as excel_count
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.document_id
            WHERE LOWER(d.filename) LIKE '%.xls%' AND dc.project_id IS NOT NULL
            GROUP BY dc.project_id
            ORDER BY excel_count DESC
        """)
        excel_by_project = cur.fetchall()
        
        # Ejemplos de archivos por tipo (simplificado)
        cur.execute("""
            SELECT DISTINCT
                CASE 
                    WHEN LOWER(d.filename) LIKE '%.pdf' THEN 'PDF'
                    WHEN LOWER(d.filename) LIKE '%.doc%' THEN 'Word'
                    WHEN LOWER(d.filename) LIKE '%.xls%' THEN 'Excel'
                    ELSE 'Otro'
                END as file_type,
                d.filename,
                dc.title,
                dc.project_id
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.document_id
            WHERE d.filename IS NOT NULL AND (
                LOWER(d.filename) LIKE '%.pdf' OR 
                LOWER(d.filename) LIKE '%.doc%' OR 
                LOWER(d.filename) LIKE '%.xls%'
            )
            ORDER BY file_type, d.filename
            LIMIT 20
        """)
        file_examples = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "file_types": file_types,
            "pdf_by_project": pdf_by_project,
            "word_by_project": word_by_project,
            "excel_by_project": excel_by_project,
            "file_examples": file_examples
        }
        
    except Exception as e:
        logging.error(f"Error analyzing file types: {e}")
        return {"error": str(e)}

def detect_question_type(question: str) -> str:
    """
    Detecta el tipo de pregunta para generar respuesta apropiada
    """
    question_lower = question.lower()
    
    # Preguntas específicas sobre tipos de archivos por proyecto
    if any(word in question_lower for word in ['pdf', 'pdfs', 'word', 'excel', 'xls', 'doc', 'docx', 'xlsx']):
        if "proyecto" in question_lower and any(word in question_lower for word in ['cuántos', 'cuantos', 'cantidad']):
            return "file_types_by_project"
    
    # Preguntas específicas sobre tipos de archivos
    if any(word in question_lower for word in ['pdf', 'pdfs', 'word', 'excel', 'xls', 'doc', 'docx', 'xlsx', 'archivo', 'archivos']):
        if any(word in question_lower for word in ['cuántos', 'cuantos', 'cantidad', 'total', 'número']):
            return "file_types"
    
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
    Genera respuesta inteligente basada en el tipo de pregunta
    """
    
    if question_type == "file_types_by_project":
        # Detectar tipo específico de archivo de la pregunta
        question_lower = question.lower()
        file_type_name = ""
        query = ""
        
        if "pdf" in question_lower:
            file_type_name = "PDFs"
            query = """
                SELECT dc.project_id, COUNT(DISTINCT dc.document_id) as count
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.document_id
                WHERE LOWER(d.filename) LIKE '%.pdf' AND dc.project_id IS NOT NULL
                GROUP BY dc.project_id
                ORDER BY count DESC
            """
        elif "excel" in question_lower or "xls" in question_lower:
            file_type_name = "Excels"
            query = """
                SELECT dc.project_id, COUNT(DISTINCT dc.document_id) as count
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.document_id
                WHERE (LOWER(d.filename) LIKE '%.xls%' OR LOWER(d.filename) LIKE '%.xlsx%') 
                AND dc.project_id IS NOT NULL
                GROUP BY dc.project_id
                ORDER BY count DESC
            """
        elif "word" in question_lower or "doc" in question_lower:
            file_type_name = "documentos Word"
            query = """
                SELECT dc.project_id, COUNT(DISTINCT dc.document_id) as count
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.document_id
                WHERE (LOWER(d.filename) LIKE '%.doc%' OR LOWER(d.filename) LIKE '%.docx%') 
                AND dc.project_id IS NOT NULL
                GROUP BY dc.project_id
                ORDER BY count DESC
            """
        
        if query:
            try:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(query)
                results = cur.fetchall()
                cur.close()
                conn.close()
                
                response = f"## 📊 {file_type_name} por Proyecto\n\n"
                
                if results:
                    total_files = sum(count for _, count in results)
                    response += f"**Total de {file_type_name.lower()}: {total_files:,}**\n\n"
                    response += f"**Distribución por proyecto:**\n"
                    
                    for project, count in results:
                        percentage = (count / total_files * 100) if total_files > 0 else 0
                        response += f"• **{project}**: {count:,} {file_type_name.lower()} ({percentage:.1f}%)\n"
                else:
                    response += f"No se encontraron {file_type_name.lower()} en ningún proyecto.\n"
                
                return response
                
            except Exception as e:
                return f"Error al consultar {file_type_name.lower()}: {str(e)}"
        else:
            return "No se pudo determinar el tipo de archivo de la pregunta."
    
    elif question_type == "file_types":
        file_stats = analyze_file_types()
        if "error" in file_stats:
            return f"Error al analizar tipos de archivos: {file_stats['error']}"
        
        response = f"## 📁 Análisis de Tipos de Archivos\n\n"
        
        if file_stats['file_types']:
            response += "**Distribución por tipo de archivo:**\n"
            total_files = sum(count for _, count, _ in file_stats['file_types'])
            for file_type, doc_count, chunk_count in file_stats['file_types']:
                percentage = (doc_count / total_files * 100) if total_files > 0 else 0
                response += f"• **{file_type}**: {doc_count:,} archivos ({percentage:.1f}%) - {chunk_count:,} fragmentos\n"
        
        # Análisis específico de PDFs
        if file_stats['pdf_by_project']:
            response += f"\n**PDFs por proyecto:**\n"
            for project, count in file_stats['pdf_by_project'][:5]:
                response += f"• {project}: {count:,} PDFs\n"
        
        # Análisis específico de Word
        if file_stats['word_by_project']:
            response += f"\n**Documentos Word por proyecto:**\n"
            for project, count in file_stats['word_by_project'][:5]:
                response += f"• {project}: {count:,} documentos Word\n"
        
        # Análisis específico de Excel
        if file_stats['excel_by_project']:
            response += f"\n**Hojas Excel por proyecto:**\n"
            for project, count in file_stats['excel_by_project'][:5]:
                response += f"• {project}: {count:,} hojas Excel\n"
        
        # Ejemplos de archivos
        if file_stats['file_examples']:
            response += f"\n**Ejemplos de archivos encontrados:**\n"
            current_type = ""
            count_by_type = {}
            for file_type, filename, title, project in file_stats['file_examples']:
                if file_type not in count_by_type:
                    count_by_type[file_type] = 0
                if count_by_type[file_type] < 3:  # Mostrar máximo 3 ejemplos por tipo
                    if file_type != current_type:
                        response += f"\n*{file_type}s:*\n"
                        current_type = file_type
                    title_short = title[:50] + "..." if len(title) > 50 else title
                    response += f"  - {title_short} ({project})\n"
                    count_by_type[file_type] += 1
        
        return response
    
    elif question_type == "statistics":
        stats = analyze_database_stats()
        if "error" in stats:
            return f"Error al acceder a las estadísticas: {stats['error']}"
        
        response = f"## 📊 Estadísticas del Sistema\n\n"
        response += f"**Total de documentos únicos:** {stats['total_documents']:,}\n"
        response += f"**Total de fragmentos indexados:** {stats['total_chunks']:,}\n\n"
        
        if stats['categories']:
            response += "**Documentos por proyecto:**\n"
            for proj, doc_count, chunk_count in stats['categories'][:5]:
                response += f"• {proj}: {doc_count:,} documentos ({chunk_count:,} fragmentos)\n"
        
        if stats['projects']:
            response += "\n**Proyectos activos:**\n"
            for proj, doc_count in stats['projects']:
                response += f"• {proj}: {doc_count:,} documentos\n"
        
        return response
    
    elif question_type == "types":
        stats = analyze_database_stats()
        if "error" in stats:
            return f"Error al acceder a los tipos: {stats['error']}"
        
        response = f"## 📋 Tipos de Documentos Disponibles\n\n"
        if stats['document_types']:
            response += "**Clasificación por tipo:**\n"
            for doc_type, count in stats['document_types']:
                response += f"• **{doc_type}**: {count:,} documentos\n"
        
        return response
    
    elif question_type == "projects":
        stats = analyze_database_stats()
        if "error" in stats:
            return f"Error al acceder a proyectos: {stats['error']}"
        
        response = f"## 🏗️ Información de Proyectos\n\n"
        if stats['projects']:
            response += "**Proyectos en el sistema:**\n"
            for proj, doc_count in stats['projects']:
                response += f"• **{proj}**: {doc_count:,} documentos\n"
        
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
            return f"Error al acceder a documentos recientes: {stats['error']}"
        
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
        
        response = f"## 🔍 Resultados para: {question}\n\n"
        response += f"**Encontré {len(relevant_docs)} documentos relevantes**\n\n"
        
        # Agrupar por proyectos
        by_project = defaultdict(list)
        for doc in relevant_docs:
            proj = doc.get('project_id', 'Sin proyecto')
            by_project[proj].append(doc)
        
        if len(by_project) > 1:
            response += "**Por proyecto:**\n"
            for proj, docs in by_project.items():
                response += f"• {proj}: {len(docs)} documentos\n"
            response += "\n"
        
        response += "**Documentos más relevantes:**\n"
        for i, doc in enumerate(relevant_docs[:10], 1):
            score = doc.get('score', 0)
            title = doc.get('title', 'Sin título')[:70]
            snippet = doc.get('snippet', '')[:150]
            response += f"{i}. **{title}** (Relevancia: {score:.2f})\n"
            if snippet:
                response += f"   _{snippet}_...\n\n"
        
        if len(relevant_docs) > 10:
            response += f"\n💡 Hay {len(relevant_docs)-10} documentos adicionales relacionados.\n"
        
        return response

@app.get("/")
def root():
    return {
        "message": "Aconex RAG Assistant v2.1",
        "version": "2.1",
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
    return {"status": "ok", "message": "Asistente RAG v2.1 funcionando"}

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
    Búsqueda conversacional inteligente
    """
    try:
        print(f"🤖 Pregunta: '{req.question}'")
        
        # 1. Detectar tipo de pregunta
        question_type = detect_question_type(req.question)
        print(f"📋 Tipo detectado: {question_type}")
        
        # 2. Realizar búsqueda semántica
        project_id = req.project_id if req.project_id != "string" else None
        search_limit = req.max_context_docs if question_type == "content_search" else min(req.max_context_docs * 3, 50)
        
        results = semantic_search(
            query=req.question,
            project_id=project_id,
            top_k=search_limit,
            probes=50
        )
        
        print(f"🔍 Encontrados: {len(results)} resultados")
        
        # 3. Generar respuesta inteligente
        answer = generate_intelligent_response(req.question, results, question_type)
        
        # 4. Preparar contexto para mostrar fuentes
        context_docs = results[:req.max_context_docs]
        
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

@app.post("/query")
async def execute_query(req: QueryRequest):
    """
    Ejecuta consultas dinámicas en la base de datos
    Permite usar plantillas predefinidas o consultas personalizadas
    """
    try:
        if req.template_name:
            # Usar plantilla predefinida
            if req.template_name == "count_by_type":
                query = """
                    SELECT 
                        CASE 
                            WHEN LOWER(d.filename) LIKE '%.pdf' THEN 'PDF'
                            WHEN LOWER(d.filename) LIKE '%.doc%' THEN 'Word'
                            WHEN LOWER(d.filename) LIKE '%.xls%' THEN 'Excel'
                            WHEN LOWER(d.filename) LIKE '%.ppt%' THEN 'PowerPoint'
                            WHEN LOWER(d.filename) LIKE '%.txt' THEN 'Texto'
                            ELSE 'Otro'
                        END as file_type,
                        COUNT(DISTINCT dc.document_id) as count
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.document_id
                    WHERE d.filename IS NOT NULL
                    GROUP BY 
                        CASE 
                            WHEN LOWER(d.filename) LIKE '%.pdf' THEN 'PDF'
                            WHEN LOWER(d.filename) LIKE '%.doc%' THEN 'Word'
                            WHEN LOWER(d.filename) LIKE '%.xls%' THEN 'Excel'
                            WHEN LOWER(d.filename) LIKE '%.ppt%' THEN 'PowerPoint'
                            WHEN LOWER(d.filename) LIKE '%.txt' THEN 'Texto'
                            ELSE 'Otro'
                        END
                    ORDER BY count DESC
                """
                result = execute_safe_query(query)
                
            elif req.template_name == "count_by_project":
                query = """
                    SELECT project_id, COUNT(DISTINCT document_id) as count
                    FROM document_chunks
                    WHERE project_id IS NOT NULL
                    GROUP BY project_id
                    ORDER BY count DESC
                """
                result = execute_safe_query(query)
                
            elif req.template_name == "search_by_keyword":
                keyword = req.parameters.get('keyword', '')
                limit = req.parameters.get('limit', 10)
                query = """
                    SELECT dc.title, dc.project_id, d.filename, 
                           substring(dc.content, 1, 200) as snippet
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.document_id
                    WHERE LOWER(dc.content) LIKE LOWER(%s)
                       OR LOWER(dc.title) LIKE LOWER(%s)
                    LIMIT %s
                """
                result = execute_safe_query(query, (f'%{keyword}%', f'%{keyword}%', limit))
                
            elif req.template_name == "recent_documents":
                limit = req.parameters.get('limit', 10)
                query = """
                    SELECT DISTINCT dc.title, dc.project_id, d.filename, dc.date_modified
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.document_id
                    WHERE dc.date_modified IS NOT NULL
                    ORDER BY dc.date_modified DESC
                    LIMIT %s
                """
                result = execute_safe_query(query, (limit,))
                
            else:
                return {"error": f"Plantilla '{req.template_name}' no encontrada"}
                
        elif req.custom_query:
            # Validaciones de seguridad básicas
            forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
            query_upper = req.custom_query.upper()
            
            for keyword in forbidden_keywords:
                if keyword in query_upper:
                    return {"error": f"Operación no permitida: {keyword}"}
            
            result = execute_safe_query(req.custom_query)
        else:
            return {"error": "Debes especificar template_name o custom_query"}
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/query/templates")
async def get_query_templates():
    """
    Obtiene la lista de plantillas de consulta disponibles
    """
    templates = {
        "count_by_type": "Cuenta documentos por tipo de archivo (PDF, Word, Excel, etc.)",
        "count_by_project": "Cuenta documentos por proyecto",
        "search_by_keyword": "Busca documentos que contengan una palabra clave (parámetros: keyword, limit)",
        "recent_documents": "Documentos más recientes (parámetro: limit)"
    }
    return templates

@app.post("/query/natural")
async def natural_language_query(req: ChatRequest):
    """
    Procesa consultas en lenguaje natural y las convierte en consultas SQL
    """
    try:
        question_lower = req.question.lower()
        
        # Detectar preguntas específicas sobre tipos de archivos
        if any(word in question_lower for word in ["pdf", "pdfs", "excel", "excels", "word", "doc", "docx"]):
            if "proyecto" in question_lower:
                # Detectar tipo específico de archivo
                if "pdf" in question_lower:
                    query = """
                        SELECT dc.project_id, COUNT(DISTINCT dc.document_id) as pdfs_count
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.document_id
                        WHERE LOWER(d.filename) LIKE '%.pdf' AND dc.project_id IS NOT NULL
                        GROUP BY dc.project_id
                        ORDER BY pdfs_count DESC
                    """
                elif "excel" in question_lower or "xls" in question_lower:
                    query = """
                        SELECT dc.project_id, COUNT(DISTINCT dc.document_id) as excel_count
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.document_id
                        WHERE (LOWER(d.filename) LIKE '%.xls%' OR LOWER(d.filename) LIKE '%.xlsx%') 
                        AND dc.project_id IS NOT NULL
                        GROUP BY dc.project_id
                        ORDER BY excel_count DESC
                    """
                elif "word" in question_lower or "doc" in question_lower:
                    query = """
                        SELECT dc.project_id, COUNT(DISTINCT dc.document_id) as word_count
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.document_id
                        WHERE (LOWER(d.filename) LIKE '%.doc%' OR LOWER(d.filename) LIKE '%.docx%') 
                        AND dc.project_id IS NOT NULL
                        GROUP BY dc.project_id
                        ORDER BY word_count DESC
                    """
                else:
                    # Todos los tipos por proyecto
                    query = """
                        SELECT 
                            dc.project_id,
                            CASE 
                                WHEN LOWER(d.filename) LIKE '%.pdf' THEN 'PDF'
                                WHEN LOWER(d.filename) LIKE '%.doc%' THEN 'Word'
                                WHEN LOWER(d.filename) LIKE '%.xls%' THEN 'Excel'
                                ELSE 'Otro'
                            END as file_type,
                            COUNT(DISTINCT dc.document_id) as count
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.document_id
                        WHERE dc.project_id IS NOT NULL AND d.filename IS NOT NULL
                        GROUP BY dc.project_id, file_type
                        ORDER BY dc.project_id, count DESC
                    """
                
                result = execute_safe_query(query)
                
                return {
                    "question": req.question,
                    "query_type": "file_count_by_project",
                    "results": result["data"] if "data" in result else [],
                    "sql_query": result.get("query", ""),
                    "total_found": len(result["data"]) if "data" in result else 0,
                    "error": result.get("error")
                }
        
        # Detectar tipo de consulta y mapear a plantillas
        elif "cuántos" in question_lower or "cantidad" in question_lower:
            if "tipo" in question_lower or any(word in question_lower for word in ["pdf", "word", "excel", "archivo"]):
                # Usar la función corregida analyze_file_types
                file_stats = analyze_file_types()
                if "error" in file_stats:
                    return {"error": file_stats["error"]}
                return {
                    "question": req.question,
                    "query_type": "file_analysis",
                    "results": file_stats,
                    "total_found": len(file_stats.get("file_types", []))
                }
            elif "proyecto" in question_lower:
                query = """
                    SELECT project_id, COUNT(DISTINCT document_id) as count
                    FROM document_chunks
                    WHERE project_id IS NOT NULL
                    GROUP BY project_id
                    ORDER BY count DESC
                """
                result = execute_safe_query(query)
                
                return {
                    "question": req.question,
                    "query_type": "project_count",
                    "results": result["data"] if "data" in result else [],
                    "sql_query": result.get("query", ""),
                    "total_found": len(result["data"]) if "data" in result else 0
                }
            else:
                # Análisis general por tipos
                file_stats = analyze_file_types()
                if "error" in file_stats:
                    return {"error": file_stats["error"]}
                return {
                    "question": req.question,
                    "query_type": "file_analysis",
                    "results": file_stats,
                    "total_found": len(file_stats.get("file_types", []))
                }
        
        elif "buscar" in question_lower or "encontrar" in question_lower:
            # Extraer palabra clave de la pregunta
            keywords = re.findall(r'\b\w+\b', question_lower)
            # Filtrar palabras comunes
            stop_words = {'buscar', 'encontrar', 'documentos', 'archivos', 'que', 'con', 'de', 'la', 'el'}
            keywords = [k for k in keywords if k not in stop_words and len(k) > 2]
            
            if keywords:
                keyword = keywords[0]
                query = """
                    SELECT dc.title, dc.project_id, d.filename, 
                           substring(dc.content, 1, 200) as snippet
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.document_id
                    WHERE LOWER(dc.content) LIKE LOWER(%s)
                       OR LOWER(dc.title) LIKE LOWER(%s)
                    ORDER BY dc.title
                    LIMIT 100
                """
                result = execute_safe_query(query, (f'%{keyword}%', f'%{keyword}%'))
                
                return {
                    "question": req.question,
                    "query_type": "keyword_search",
                    "results": result["data"] if "data" in result else [],
                    "sql_query": result.get("query", ""),
                    "total_found": len(result["data"]) if "data" in result else 0
                }
            else:
                result = {"error": "No se pudo extraer palabra clave de la búsqueda"}
        
        elif "reciente" in question_lower or "último" in question_lower:
            query = """
                SELECT DISTINCT dc.title, dc.project_id, d.filename, dc.date_modified
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.document_id
                WHERE dc.date_modified IS NOT NULL
                ORDER BY dc.date_modified DESC
                LIMIT 50
            """
            result = execute_safe_query(query)
            
            return {
                "question": req.question,
                "query_type": "recent_documents",
                "results": result["data"] if "data" in result else [],
                "sql_query": result.get("query", ""),
                "total_found": len(result["data"]) if "data" in result else 0
            }
        
        else:
            # Búsqueda general usando búsqueda semántica
            semantic_results = semantic_search(req.question, req.project_id, req.max_context_docs)
            return {
                "question": req.question,
                "query_type": "semantic_search",
                "results": semantic_results,
                "total_found": len(semantic_results)
            }
        
        if "error" in result:
            return result
        
        # Formatear respuesta (esta parte no debería ejecutarse con los returns anteriores)
        return {
            "question": req.question,
            "query_type": "template_based",
            "results": result["data"] if "data" in result else [],
            "sql_query": result.get("query", ""),
            "total_found": len(result["data"]) if "data" in result else 0
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Aconex RAG Assistant v2.1...")
    uvicorn.run(app, host="0.0.0.0", port=8000)