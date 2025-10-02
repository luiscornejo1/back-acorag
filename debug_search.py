#!/usr/bin/env python3
"""
Script de debug para búsqueda semántica
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

def debug_search(query: str, project_id: str = None, top_k: int = 5):
    """Debug paso a paso de la búsqueda"""
    
    print(f"🔍 DEBUG: Búsqueda para '{query}'")
    print(f"📋 Parámetros: project_id={project_id}, top_k={top_k}")
    
    # Conectar
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Verificar datos en BD
    cur.execute("SELECT COUNT(*) as total FROM document_chunks")
    total_chunks = cur.fetchone()['total']
    print(f"📊 Total chunks en BD: {total_chunks:,}")
    
    # 2. Cargar modelo y generar embedding
    print("🧠 Cargando modelo...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    print("🔢 Generando embedding...")
    query_embedding = model.encode(query, normalize_embeddings=True)
    print(f"✅ Embedding generado: {len(query_embedding)} dimensiones")
    
    # 3. Búsqueda directa sin filtros
    print("\n🔍 Búsqueda SIN filtros:")
    sql_simple = """
        SELECT 
            dc.document_id,
            d.title,
            dc.content,
            1 - (dc.embedding <=> %s::vector) as similarity_score
        FROM document_chunks dc
        JOIN documents d ON d.document_id = dc.document_id
        ORDER BY dc.embedding <=> %s::vector
        LIMIT %s
    """
    
    params_simple = [query_embedding.tolist(), query_embedding.tolist(), top_k]
    
    try:
        cur.execute(sql_simple, params_simple)
        results = cur.fetchall()
        
        print(f"✅ Resultados encontrados: {len(results)}")
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. Score: {result['similarity_score']:.3f}")
            print(f"      Título: {result['title'][:60]}...")
            print(f"      Doc ID: {result['document_id']}")
    
    except Exception as e:
        print(f"❌ Error en búsqueda simple: {e}")
    
    # 4. Búsqueda con filtro de proyecto si se especifica
    if project_id:
        print(f"\n🔍 Búsqueda CON filtro de proyecto: '{project_id}'")
        sql_filtered = """
            SELECT 
                dc.document_id,
                d.title,
                dc.content,
                dc.project_id,
                1 - (dc.embedding <=> %s::vector) as similarity_score
            FROM document_chunks dc
            JOIN documents d ON d.document_id = dc.document_id
            WHERE dc.project_id = %s
            ORDER BY dc.embedding <=> %s::vector
            LIMIT %s
        """
        
        params_filtered = [query_embedding.tolist(), project_id, query_embedding.tolist(), top_k]
        
        try:
            cur.execute(sql_filtered, params_filtered)
            results_filtered = cur.fetchall()
            
            print(f"✅ Resultados con filtro: {len(results_filtered)}")
            for i, result in enumerate(results_filtered[:3], 1):
                print(f"   {i}. Score: {result['similarity_score']:.3f}")
                print(f"      Título: {result['title'][:60]}...")
                print(f"      Proyecto: {result['project_id']}")
        
        except Exception as e:
            print(f"❌ Error en búsqueda filtrada: {e}")
        
        # Verificar qué proyectos existen
        print(f"\n📋 Proyectos disponibles:")
        cur.execute("""
            SELECT project_id, COUNT(*) as count 
            FROM document_chunks 
            GROUP BY project_id 
            ORDER BY count DESC 
            LIMIT 10
        """)
        projects = cur.fetchall()
        for proj in projects:
            print(f"   • {proj['project_id']}: {proj['count']:,} chunks")
    
    conn.close()

if __name__ == "__main__":
    debug_search("planos", None, 5)
    print("\n" + "="*60)
    debug_search("planos", "string", 5)  # Usar string como en tu ejemplo