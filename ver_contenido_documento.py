"""
Script para ver el contenido extraído de un documento específico
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()

def ver_contenido_documento(titulo_buscar):
    """Muestra el contenido extraído de un documento"""
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("❌ ERROR: DATABASE_URL no configurada")
        return
    
    conn = psycopg2.connect(url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Buscar documento
        cur.execute("""
            SELECT document_id, title, filename
            FROM documents
            WHERE LOWER(title) LIKE LOWER(%s) OR LOWER(filename) LIKE LOWER(%s)
            ORDER BY date_modified DESC
            LIMIT 1
        """, (f'%{titulo_buscar}%', f'%{titulo_buscar}%'))
        
        doc = cur.fetchone()
        
        if not doc:
            print(f"❌ No se encontró documento con '{titulo_buscar}'")
            return
        
        print(f"\n📄 Documento encontrado:")
        print(f"   Título: {doc['title']}")
        print(f"   Archivo: {doc['filename']}")
        print(f"   ID: {doc['document_id']}")
        
        # Obtener chunks
        cur.execute("""
            SELECT chunk_id, content, embedding IS NOT NULL as tiene_embedding
            FROM document_chunks
            WHERE document_id = %s
            ORDER BY chunk_id
        """, (doc['document_id'],))
        
        chunks = cur.fetchall()
        
        print(f"\n📝 Total de chunks: {len(chunks)}")
        
        if not chunks:
            print("⚠️  ¡NO HAY CHUNKS! El documento no fue procesado correctamente.")
            return
        
        # Mostrar primeros 3 chunks
        print("\n" + "=" * 100)
        print("📋 PRIMEROS 3 CHUNKS:")
        print("=" * 100)
        
        for i, chunk in enumerate(chunks[:3], 1):
            contenido = chunk['content'][:500] if chunk['content'] else '[VACÍO]'
            tiene_emb = "✅" if chunk['tiene_embedding'] else "❌"
            
            print(f"\nChunk {i} (Embedding: {tiene_emb}):")
            print(f"  Longitud: {len(chunk['content']) if chunk['content'] else 0} caracteres")
            print(f"  Contenido:")
            print(f"  {contenido}...")
            print("-" * 100)
        
        # Verificar si hay contenido vacío
        chunks_vacios = sum(1 for c in chunks if not c['content'] or len(c['content'].strip()) < 10)
        chunks_sin_embedding = sum(1 for c in chunks if not c['tiene_embedding'])
        
        if chunks_vacios > 0:
            print(f"\n⚠️  ADVERTENCIA: {chunks_vacios}/{len(chunks)} chunks tienen contenido vacío o muy corto")
        
        if chunks_sin_embedding > 0:
            print(f"\n⚠️  ADVERTENCIA: {chunks_sin_embedding}/{len(chunks)} chunks NO tienen embedding")
        
        if chunks_vacios == 0 and chunks_sin_embedding == 0:
            print(f"\n✅ Todos los chunks tienen contenido y embeddings correctos")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("🔍 VER CONTENIDO DE DOCUMENTO")
    print("=" * 100)
    print("\nEscribe parte del título o nombre del archivo a buscar:")
    titulo = input("> ").strip()
    
    if titulo:
        ver_contenido_documento(titulo)
    else:
        print("❌ No ingresaste ningún término de búsqueda")
