"""
Test simple de búsqueda del documento Aconex
"""
import asyncio
import os
from dotenv import load_dotenv
import asyncpg
from sentence_transformers import SentenceTransformer

load_dotenv()

async def test_aconex_search():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print("=" * 80)
    print("VERIFICANDO DOCUMENTOS ACONEX EN LA BASE DE DATOS")
    print("=" * 80)
    
    # Buscar TODOS los documentos con "aconex"
    all_aconex_docs = await conn.fetch("""
        SELECT document_id, title, filename
        FROM documents 
        WHERE title ILIKE '%aconex%'
        ORDER BY date_modified DESC
    """)
    
    print(f"\nTODOS los documentos con 'aconex': {len(all_aconex_docs)}")
    for i, doc in enumerate(all_aconex_docs, 1):
        print(f"  {i}. Titulo: {doc['title']}")
        print(f"     ID: {doc['document_id']}")
        print(f"     Archivo: {doc['filename']}\n")
    
    # El documento que nos interesa
    doc_id_nuevo = '3c3580e4a12a27f2636950026a084ff3'
    
    # Verificar chunks
    chunks_count = await conn.fetchval("""
        SELECT COUNT(*) FROM document_chunks WHERE document_id = $1
    """, doc_id_nuevo)
    
    print(f"Chunks del documento 'Fechas, Listado Total': {chunks_count}")
    
    # Generar embedding de la query
    print("\n" + "=" * 80)
    print("GENERANDO EMBEDDING Y BUSCANDO")
    print("=" * 80)
    
    model = SentenceTransformer('hiiamsid/sentence_similarity_spanish_es')
    query_text = "aconex fechas"
    query_embedding = model.encode(query_text).tolist()
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    print(f"\nQuery: '{query_text}'")
    print(f"Embedding generado: {len(query_embedding)} dimensiones\n")
    
    # Buscar en TODO el documento nuevo específicamente
    print("Scores del documento 'Fechas, Listado Total' (todos los chunks):")
    doc_results = await conn.fetch("""
        SELECT 
            LEFT(dc.content, 80) as content_preview,
            1 - (dc.embedding <=> $1::vector) as similarity
        FROM document_chunks dc
        WHERE dc.document_id = $2
        ORDER BY similarity DESC
    """, embedding_str, doc_id_nuevo)
    
    for i, row in enumerate(doc_results, 1):
        print(f"  Chunk {i}: Similarity = {row['similarity']:.4f}")
        print(f"    Content: {row['content_preview']}...\n")
    
    # Búsqueda en TODOS los documentos (TOP 50)
    print("\n" + "=" * 80)
    print("BUSQUEDA EN TODOS LOS DOCUMENTOS (TOP 50)")
    print("=" * 80 + "\n")
    
    all_results = await conn.fetch("""
        SELECT 
            d.document_id,
            d.title,
            1 - (dc.embedding <=> $1::vector) as similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.document_id
        ORDER BY similarity DESC
        LIMIT 50
    """, embedding_str)
    
    aconex_found = False
    aconex_position = None
    
    for i, row in enumerate(all_results, 1):
        is_aconex_fechas = row['document_id'] == doc_id_nuevo
        marker = ">>> ACONEX FECHAS <<<" if is_aconex_fechas else ""
        
        if is_aconex_fechas:
            aconex_found = True
            aconex_position = i
            
        print(f"  {i}. Similarity: {row['similarity']:.4f} - {row['title'][:70]} {marker}")
    
    print("\n" + "=" * 80)
    if aconex_found:
        print(f"RESULTADO: El documento 'Aconex Fechas' APARECE en posicion {aconex_position}")
    else:
        print("RESULTADO: El documento 'Aconex Fechas' NO APARECE en el top 50")
    print("=" * 80)
    
    # Prueba con DISTINCT ON
    print("\n" + "=" * 80)
    print("BUSQUEDA CON DISTINCT ON (como en la busqueda real)")
    print("=" * 80 + "\n")
    
    distinct_results = await conn.fetch("""
        SELECT DISTINCT ON (d.document_id)
            d.document_id,
            d.title,
            1 - (dc.embedding <=> $1::vector) as similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.document_id
        ORDER BY d.document_id, similarity DESC
        LIMIT 50
    """, embedding_str)
    
    aconex_found_distinct = False
    aconex_position_distinct = None
    
    for i, row in enumerate(distinct_results, 1):
        is_aconex_fechas = row['document_id'] == doc_id_nuevo
        marker = ">>> ACONEX FECHAS <<<" if is_aconex_fechas else ""
        
        if is_aconex_fechas:
            aconex_found_distinct = True
            aconex_position_distinct = i
            
        print(f"  {i}. Similarity: {row['similarity']:.4f} - {row['title'][:70]} {marker}")
    
    print("\n" + "=" * 80)
    if aconex_found_distinct:
        print(f"RESULTADO: Con DISTINCT ON, 'Aconex Fechas' APARECE en posicion {aconex_position_distinct}")
    else:
        print("RESULTADO: Con DISTINCT ON, 'Aconex Fechas' NO APARECE en el top 50")
    print("=" * 80)
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(test_aconex_search())
