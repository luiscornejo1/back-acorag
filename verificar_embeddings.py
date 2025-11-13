"""
Script para verificar si los embeddings fueron regenerados
Compara las dimensiones de los embeddings de diferentes documentos
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import json

load_dotenv()

def verificar_embeddings():
    """Verifica las dimensiones de embeddings de documentos recientes"""
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("❌ ERROR: DATABASE_URL no configurada")
        return
    
    conn = psycopg2.connect(url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Obtener chunks de documentos específicos
        documentos_test = [
            'competenciadigital',
            'COMPRENSION_LECTORA_INTELIGENCIA_ARTIFICIAL',
            'LUIS PORTFOLIO'
        ]
        
        print("🔍 VERIFICANDO DIMENSIONES DE EMBEDDINGS\n")
        print("=" * 100)
        
        for doc_name in documentos_test:
            cur.execute("""
                SELECT 
                    d.title,
                    dc.chunk_id,
                    dc.embedding,
                    LENGTH(dc.embedding::text) as embedding_length
                FROM document_chunks dc
                JOIN documents d ON d.document_id = dc.document_id
                WHERE d.title LIKE %s
                LIMIT 1
            """, (f'%{doc_name}%',))
            
            result = cur.fetchone()
            
            if result:
                # Contar dimensiones del embedding
                embedding_str = result['embedding']
                if embedding_str:
                    # El embedding es un string como '[0.1, 0.2, ...]'
                    # Contar cuántos números hay
                    try:
                        embedding_list = json.loads(embedding_str)
                        dimensiones = len(embedding_list)
                    except:
                        # Si falla JSON, contar comas
                        dimensiones = embedding_str.count(',') + 1
                    
                    print(f"\n📄 {result['title']}")
                    print(f"   Chunk ID: {result['chunk_id']}")
                    print(f"   Dimensiones: {dimensiones}")
                    print(f"   Longitud string: {result['embedding_length']} chars")
                    
                    # Verificar modelo
                    if dimensiones == 768:
                        print(f"   ✅ Modelo: hiiamsid/sentence_similarity_spanish_es")
                    elif dimensiones == 384:
                        print(f"   ⚠️  Modelo: paraphrase-multilingual-MiniLM-L12-v2 (VIEJO)")
                    else:
                        print(f"   ❓ Modelo: DESCONOCIDO ({dimensiones} dimensiones)")
                else:
                    print(f"\n📄 {result['title']}")
                    print(f"   ❌ NO TIENE EMBEDDING")
            else:
                print(f"\n❌ No se encontró documento: {doc_name}")
        
        print("\n" + "=" * 100)
        
        # Resumen general
        cur.execute("""
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(embedding) as chunks_con_embedding,
                COUNT(*) - COUNT(embedding) as chunks_sin_embedding
            FROM document_chunks
        """)
        
        stats = cur.fetchone()
        print(f"\n📊 RESUMEN GENERAL:")
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Con embedding: {stats['chunks_con_embedding']}")
        print(f"   Sin embedding: {stats['chunks_sin_embedding']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    verificar_embeddings()
