#!/usr/bin/env python3
"""
Sistema de consultas dinámicas para la base de datos RAG
Permite ejecutar consultas personalizadas de forma segura
"""
import psycopg2
from typing import Dict, List, Any
from app.search_core import get_conn

class DynamicQueryEngine:
    """Motor de consultas dinámicas con plantillas predefinidas"""
    
    def __init__(self):
        self.query_templates = {
            "count_by_type": """
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
                GROUP BY file_type
                ORDER BY count DESC
            """,
            
            "count_by_project": """
                SELECT project_id, COUNT(DISTINCT document_id) as count
                FROM document_chunks
                WHERE project_id IS NOT NULL
                GROUP BY project_id
                ORDER BY count DESC
            """,
            
            "search_by_keyword": """
                SELECT dc.title, dc.project_id, d.filename, 
                       substring(dc.content, 1, 200) as snippet
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.document_id
                WHERE LOWER(dc.content) LIKE LOWER('%{keyword}%')
                   OR LOWER(dc.title) LIKE LOWER('%{keyword}%')
                LIMIT {limit}
            """,
            
            "files_by_project_and_type": """
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
                WHERE dc.project_id = '{project}' AND d.filename IS NOT NULL
                GROUP BY dc.project_id, file_type
                ORDER BY count DESC
            """,
            
            "recent_documents": """
                SELECT DISTINCT dc.title, dc.project_id, d.filename, dc.date_modified
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.document_id
                WHERE dc.date_modified IS NOT NULL
                ORDER BY dc.date_modified DESC
                LIMIT {limit}
            """,
            
            "documents_with_word": """
                SELECT DISTINCT dc.title, dc.project_id, d.filename,
                       COUNT(*) as chunks_with_word
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.document_id
                WHERE LOWER(dc.content) LIKE LOWER('%{word}%')
                GROUP BY dc.title, dc.project_id, d.filename
                ORDER BY chunks_with_word DESC
                LIMIT {limit}
            """
        }
    
    def execute_template_query(self, template_name: str, **params) -> List[Dict]:
        """Ejecuta una consulta basada en plantilla"""
        if template_name not in self.query_templates:
            return {"error": f"Plantilla '{template_name}' no encontrada"}
        
        try:
            # Obtener la plantilla y formatear parámetros
            query = self.query_templates[template_name].format(**params)
            
            conn = get_conn()
            cur = conn.cursor()
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
            return {"error": str(e), "query": query if 'query' in locals() else ""}
    
    def execute_custom_query(self, query: str) -> List[Dict]:
        """Ejecuta una consulta SQL personalizada (CON RESTRICCIONES DE SEGURIDAD)"""
        # Validaciones de seguridad básicas
        forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        query_upper = query.upper()
        
        for keyword in forbidden_keywords:
            if keyword in query_upper:
                return {"error": f"Operación no permitida: {keyword}"}
        
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(query)
            
            columns = [desc[0] for desc in cur.description]
            results = []
            for row in cur.fetchall():
                results.append(dict(zip(columns, row)))
            
            cur.close()
            conn.close()
            
            return {"success": True, "data": results, "query": query}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_available_templates(self) -> Dict[str, str]:
        """Devuelve las plantillas disponibles con sus descripciones"""
        descriptions = {
            "count_by_type": "Cuenta documentos por tipo de archivo (PDF, Word, Excel, etc.)",
            "count_by_project": "Cuenta documentos por proyecto",
            "search_by_keyword": "Busca documentos que contengan una palabra clave (parámetros: keyword, limit)",
            "files_by_project_and_type": "Análisis de tipos de archivo por proyecto específico (parámetro: project)",
            "recent_documents": "Documentos más recientes (parámetro: limit)",
            "documents_with_word": "Documentos que contienen una palabra específica (parámetros: word, limit)"
        }
        return descriptions

# Ejemplos de uso:
if __name__ == "__main__":
    engine = DynamicQueryEngine()
    
    # Ejemplo 1: Contar por tipo
    result = engine.execute_template_query("count_by_type")
    print("Documentos por tipo:", result)
    
    # Ejemplo 2: Buscar palabra clave
    result = engine.execute_template_query("search_by_keyword", keyword="calidad", limit=5)
    print("Búsqueda de 'calidad':", result)
    
    # Ejemplo 3: Consulta personalizada
    custom_query = """
        SELECT project_id, COUNT(*) as total_chunks
        FROM document_chunks 
        GROUP BY project_id 
        ORDER BY total_chunks DESC
    """
    result = engine.execute_custom_query(custom_query)
    print("Consulta personalizada:", result)