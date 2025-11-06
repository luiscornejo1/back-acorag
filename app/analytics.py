"""
Endpoints adicionales para analytics y mejoras del sistema
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import psycopg2
import os
from datetime import datetime, timedelta

router = APIRouter()

# =============================================
# ANALYTICS
# =============================================

@router.get("/analytics/popular-searches")
def get_popular_searches(days: int = 7, limit: int = 10):
    """Obtiene las búsquedas más populares de los últimos N días"""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_logs (
                id SERIAL PRIMARY KEY,
                query TEXT NOT NULL,
                project_id TEXT,
                results_count INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Obtener búsquedas populares
        cursor.execute("""
            SELECT query, COUNT(*) as count
            FROM search_logs
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY query
            ORDER BY count DESC
            LIMIT %s
        """, (days, limit))
        
        results = [{"query": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/feedback-stats")
def get_feedback_stats():
    """Obtiene estadísticas de feedback de usuarios"""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor()
        
        # Promedio de rating
        cursor.execute("""
            SELECT 
                AVG(rating) as avg_rating,
                COUNT(*) as total_feedbacks,
                SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) as negative
            FROM chat_feedback
        """)
        
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row and row[1] > 0:
            return {
                "average_rating": round(float(row[0]), 2),
                "total_feedbacks": row[1],
                "positive_count": row[2],
                "negative_count": row[3],
                "satisfaction_rate": round((row[2] / row[1]) * 100, 1)
            }
        else:
            return {
                "average_rating": 0,
                "total_feedbacks": 0,
                "positive_count": 0,
                "negative_count": 0,
                "satisfaction_rate": 0
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# SUGERENCIAS DE BÚSQUEDA
# =============================================

@router.get("/suggestions")
def get_search_suggestions(q: str, limit: int = 5):
    """Obtiene sugerencias de búsqueda basadas en documentos existentes"""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor()
        
        # Buscar títulos similares
        cursor.execute("""
            SELECT DISTINCT title
            FROM documents
            WHERE title ILIKE %s
            LIMIT %s
        """, (f"%{q}%", limit))
        
        suggestions = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# HISTORIAL DE CHAT
# =============================================

class ChatHistory(BaseModel):
    user_id: str
    question: str
    answer: str
    session_id: str

@router.post("/chat/history")
def save_chat_history(chat: ChatHistory):
    """Guarda historial de conversaciones"""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        cursor.execute(
            "INSERT INTO chat_history (user_id, question, answer, session_id) VALUES (%s, %s, %s, %s)",
            (chat.user_id, chat.question, chat.answer, chat.session_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history/{user_id}")
def get_chat_history(user_id: str, limit: int = 20):
    """Obtiene historial de chat de un usuario"""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT question, answer, created_at
            FROM chat_history
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))
        
        history = [
            {
                "question": row[0],
                "answer": row[1],
                "timestamp": row[2].isoformat()
            }
            for row in cursor.fetchall()
        ]
        
        cursor.close()
        conn.close()
        
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# STATS DE DOCUMENTOS
# =============================================

@router.get("/stats/documents")
def get_document_stats():
    """Obtiene estadísticas generales de documentos"""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor()
        
        # Total de documentos
        cursor.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]
        
        # Documentos por tipo
        cursor.execute("""
            SELECT doc_type, COUNT(*) 
            FROM documents 
            WHERE doc_type IS NOT NULL AND doc_type != ''
            GROUP BY doc_type 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        """)
        by_type = [{"type": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Documentos por proyecto
        cursor.execute("""
            SELECT project_id, COUNT(*) 
            FROM documents 
            GROUP BY project_id 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        """)
        by_project = [{"project": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return {
            "total_documents": total_docs,
            "by_type": by_type,
            "by_project": by_project
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
