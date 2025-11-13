"""
Test directo de búsqueda del documento Aconex
"""
import asyncio
import os
from dotenv import load_dotenv
import asyncpg
from sentence_transformers import SentenceTransformer

load_dotenv()

async def test_aconex_search():
    # Conectar a la base de datos
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    # 1. Verificar que el documento existe
    print("=" * 80)
    print("1️⃣ VERIFICANDO EXISTENCIA DEL DOCUMENTO ACONEX")
    print("=" * 80)
    
    doc = await conn.fetchrow("""
        SELECT document_id, title, COUNT(*) OVER() as total_chunks
        FROM documents 
        WHERE title ILIKE '%aconex%'
        LIMIT 1
    """)
    
    if doc:
        print(f"✅ Documento encontrado:")
        print(f"   ID: {doc['document_id']}")
        print(f"   Título: {doc['title']}")
        print(f"   Total chunks: {doc['total_chunks']}")
    else:
        print("❌ NO se encontró documento Aconex")
        await conn.close()
        return
    
    doc_id = doc['document_id']
    
    # 2. Verificar chunks del documento
    print("\n" + "=" * 80)
    print("2️⃣ VERIFICANDO CHUNKS DEL DOCUMENTO")
    print("=" * 80)
    
    # Buscar TODOS los documentos con "aconex"
    all_aconex_docs = await conn.fetch("""
        SELECT document_id, title, filename
        FROM documents 
        WHERE title ILIKE '%aconex%'
        ORDER BY date_modified DESC
    """)
    
    print(f"\n📚 TODOS los documentos con 'aconex' ({len(all_aconex_docs)}):")
    for i, doc in enumerate(all_aconex_docs, 1):
        print(f"  {i}. Título: {doc['title']}")
        print(f"     ID: {doc['document_id']}")
        print(f"     Archivo: {doc['filename']}")
        print()
    
    chunks = await conn.fetch("""
        SELECT chunk_id, LEFT(content, 100) as content_preview, 
               embedding IS NOT NULL as has_embedding
        FROM document_chunks
        WHERE document_id = $1
        LIMIT 5
    """, doc_id)
    
    print(f"📊 Chunks del documento '{doc['title']}': {len(chunks)}")
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i}:")
        print(f"  ID: {chunk['chunk_id']}")
        print(f"  Contenido: {chunk['content_preview']}...")
        print(f"  Tiene embedding: {chunk['has_embedding']}")
    
    # 3. Hacer búsqueda vectorial simple SIN DISTINCT
    print("\n" + "=" * 80)
    print("3️⃣ BÚSQUEDA VECTORIAL SIMPLE (SIN DISTINCT)")
    print("=" * 80)
    
    # Generar embedding de la query
    model = SentenceTransformer('hiiamsid/sentence_similarity_spanish_es')
    query_text = "aconex fechas"
    query_embedding = model.encode(query_text).tolist()
    
    print(f"🔍 Query: '{query_text}'")
    print(f"📊 Embedding generado: {len(query_embedding)} dimensiones")
    
    # Convertir a string para asyncpg
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    # Búsqueda simple - buscar el documento específico
    doc_id_nuevo = '3c3580e4a12a27f2636950026a084ff3'  # El documento "Fechas, Listado Total"
    results = await conn.fetch("""
        SELECT 
            dc.chunk_id,
            d.title,
            LEFT(dc.content, 100) as content_preview,
            1 - (dc.embedding <=> $1::vector) as similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.document_id
        WHERE d.document_id = $2
        ORDER BY similarity DESC
        LIMIT 10
    """, embedding_str, doc_id_nuevo)
    
    print(f"\n📋 Resultados para documento Aconex (Fechas...):")
    for i, row in enumerate(results, 1):
        print(f"\n  {i}. Similarity: {row['similarity']:.4f}")
        print(f"     Título: {row['title']}")
        print(f"     Contenido: {row['content_preview']}...")
    
    # 4. Búsqueda en TODOS los documentos
    print("\n" + "=" * 80)
    print("4️⃣ BÚSQUEDA VECTORIAL EN TODOS LOS DOCUMENTOS (TOP 50)")
    print("=" * 80)
    
    all_results = await conn.fetch("""
        SELECT 
            d.document_id,
            d.title,
            LEFT(dc.content, 80) as content_preview,
            1 - (dc.embedding <=> $1::vector) as similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.document_id
        ORDER BY similarity DESC
        LIMIT 50
    """, embedding_str)
    
    print(f"\n📋 Top 50 resultados de TODA la base de datos:")
    aconex_found = False
    for i, row in enumerate(all_results, 1):
        is_aconex = 'aconex' in row['title'].lower()
        marker = "🎯" if is_aconex else "  "
        if is_aconex:
            aconex_found = True
        print(f"{marker} {i}. Similarity: {row['similarity']:.4f} - {row['title'][:60]}")
    
    if not aconex_found:
        print("\n❌ El documento Aconex NO aparece en el top 50 de búsqueda vectorial")
    else:
        print("\n✅ El documento Aconex SÍ aparece en los resultados")
    
    # 5. Prueba con DISTINCT ON (como en la búsqueda real)
    print("\n" + "=" * 80)
    print("5️⃣ BÚSQUEDA CON DISTINCT ON (COMO EN LA BÚSQUEDA REAL)")
    print("=" * 80)
    
    distinct_results = await conn.fetch("""
        SELECT DISTINCT ON (d.document_id)
            d.document_id,
            d.title,
            LEFT(dc.content, 80) as content_preview,
            1 - (dc.embedding <=> $1::vector) as similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.document_id
        ORDER BY d.document_id, similarity DESC
        LIMIT 50
    """, embedding_str)
    
    print(f"\n📋 Top 50 con DISTINCT ON:")
    aconex_found_distinct = False
    for i, row in enumerate(distinct_results, 1):
        is_aconex = 'aconex' in row['title'].lower()
        marker = "🎯" if is_aconex else "  "
        if is_aconex:
            aconex_found_distinct = True
        print(f"{marker} {i}. Similarity: {row['similarity']:.4f} - {row['title'][:60]}")
    
    if not aconex_found_distinct:
        print("\n❌ DISTINCT ON elimina el documento Aconex")
    else:
        print("\n✅ DISTINCT ON mantiene el documento Aconex")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(test_aconex_search())
