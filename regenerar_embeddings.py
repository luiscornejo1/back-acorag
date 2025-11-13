"""
Script para regenerar embeddings de documentos existentes con el modelo nuevo
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

load_dotenv()

def regenerar_embeddings():
    """Regenera los embeddings de todos los chunks con el modelo nuevo"""
    url = os.environ.get("DATABASE_URL")
    model_name = os.environ.get("EMBEDDING_MODEL", "hiiamsid/sentence_similarity_spanish_es")
    
    if not url:
        print("❌ ERROR: DATABASE_URL no configurada")
        return
    
    print(f"🔧 Cargando modelo: {model_name}")
    model = SentenceTransformer(model_name, trust_remote_code=True)
    print(f"✅ Modelo cargado - Dimensiones: {model.get_sentence_embedding_dimension()}")
    
    conn = psycopg2.connect(url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Obtener todos los chunks
        cur.execute("SELECT chunk_id, content FROM document_chunks ORDER BY chunk_id")
        chunks = cur.fetchall()
        
        total = len(chunks)
        print(f"\n📊 Total de chunks a procesar: {total}")
        
        if total == 0:
            print("⚠️  No hay chunks en la base de datos")
            return
        
        # Procesar en batches
        batch_size = 32
        updated = 0
        
        for i in range(0, total, batch_size):
            batch = chunks[i:i+batch_size]
            batch_texts = [c['content'] for c in batch]
            batch_ids = [c['chunk_id'] for c in batch]
            
            # Generar embeddings
            embeddings = model.encode(batch_texts, normalize_embeddings=True, convert_to_numpy=True)
            
            # Actualizar cada chunk
            for chunk_id, embedding in zip(batch_ids, embeddings):
                embedding_str = '[' + ','.join(str(float(x)) for x in embedding) + ']'
                
                cur.execute(
                    "UPDATE document_chunks SET embedding = %s::vector WHERE chunk_id = %s",
                    (embedding_str, chunk_id)
                )
            
            updated += len(batch)
            progress = (updated / total) * 100
            print(f"   Procesados: {updated}/{total} ({progress:.1f}%)")
            
            # Commit cada batch
            conn.commit()
        
        print(f"\n✨ ¡Completado! {updated} chunks actualizados con embeddings nuevos")
        print(f"🎯 Modelo usado: {model_name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("🔄 Regenerando embeddings con el modelo nuevo...")
    print("⚠️  Esto puede tomar varios minutos dependiendo del número de documentos\n")
    
    respuesta = input("¿Continuar? (escribe 'SI'): ")
    
    if respuesta.strip().upper() == "SI":
        regenerar_embeddings()
    else:
        print("❌ Operación cancelada")
