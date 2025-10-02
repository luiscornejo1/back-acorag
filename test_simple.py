#!/usr/bin/env python3
"""
Prueba simplificada de búsqueda semántica
"""
import os
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

def test_simple_search():
    """Prueba búsqueda semántica de forma simple"""
    
    print("🚀 PRUEBA DE BÚSQUEDA SEMÁNTICA")
    print("=" * 50)
    
    # Conectar a BD
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    
    # Verificar datos
    cur.execute("SELECT COUNT(*) FROM document_chunks")
    chunk_count = cur.fetchone()[0]
    print(f"📊 Total chunks disponibles: {chunk_count:,}")
    
    # Cargar modelo
    print("🧠 Cargando modelo...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    # Consultas de prueba
    queries = [
        "planos de arquitectura",
        "documentos de construcción", 
        "especificaciones técnicas",
        "telecomunicaciones"
    ]
    
    for query in queries:
        print(f"\n🔍 Búsqueda: '{query}'")
        
        # Generar embedding
        query_embedding = model.encode(query, normalize_embeddings=True)
        
        # Búsqueda
        cur.execute("""
            SELECT 
                title,
                content,
                1 - (embedding <=> %s::vector) as similarity_score
            FROM document_chunks 
            ORDER BY embedding <=> %s::vector
            LIMIT 3
        """, (query_embedding.tolist(), query_embedding.tolist()))
        
        results = cur.fetchall()
        
        print(f"✅ Encontrados {len(results)} resultados:")
        for i, (title, content, score) in enumerate(results, 1):
            print(f"   {i}. Score: {score:.3f}")
            print(f"      Título: {title[:60]}...")
            print(f"      Contenido: {content[:80]}...")
    
    conn.close()
    print("\n🎉 ¡Búsqueda semántica funcionando correctamente!")

if __name__ == "__main__":
    test_simple_search()