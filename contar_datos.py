"""
Contar datos en las tablas
"""
import psycopg2
import os

print("📊 CONTANDO DATOS EN LA BASE DE DATOS")
print("="*60)

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

try:
    # Contar documentos
    cur.execute("SELECT COUNT(*) FROM documents")
    doc_count = cur.fetchone()[0]
    print(f"📄 Documentos: {doc_count:,}")
    
    # Contar chunks
    cur.execute("SELECT COUNT(*) FROM document_chunks")
    chunk_count = cur.fetchone()[0]
    print(f"📦 Chunks: {chunk_count:,}")
    
    # Contar chunks con embedding
    cur.execute("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
    emb_count = cur.fetchone()[0]
    print(f"🔢 Chunks con embedding: {emb_count:,}")
    
    # Contar chunks sin embedding
    cur.execute("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NULL")
    no_emb_count = cur.fetchone()[0]
    print(f"❌ Chunks SIN embedding: {no_emb_count:,}")
    
    # Ver un ejemplo de chunk
    print("\n" + "="*60)
    print("📝 EJEMPLO DE CHUNK:")
    print("="*60)
    cur.execute("""
        SELECT chunk_id, title, project_id, 
               LEFT(content, 100) as content_preview,
               embedding IS NOT NULL as tiene_embedding
        FROM document_chunks 
        LIMIT 1
    """)
    
    row = cur.fetchone()
    if row:
        print(f"Chunk ID: {row[0]}")
        print(f"Title: {row[1]}")
        print(f"Project ID: {row[2]}")
        print(f"Content: {row[3]}...")
        print(f"Tiene embedding: {row[4]}")
    else:
        print("❌ NO HAY CHUNKS")
    
    print("\n" + "="*60)
    
    if chunk_count == 0:
        print("❌ ERROR: NO HAY DATOS - La ingesta NO funcionó")
    elif emb_count == 0:
        print("❌ ERROR: NO HAY EMBEDDINGS - Los vectores no se generaron")
    else:
        print("✅ OK: Hay datos y embeddings")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    cur.close()
    conn.close()
