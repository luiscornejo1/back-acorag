"""
Regenerar SOLO los embeddings (sin re-chunking)
Mucho más rápido: ~30-40 minutos para 25,653 chunks
"""
import os
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
from tqdm import tqdm
import time

load_dotenv()

RAILWAY_DB_URL = "postgres://postgres:wYmPtyJn8HbVZPpMC.ghW8InX-DaMyoS@switchyard.proxy.rlwy.net:32780/railway"
BATCH_SIZE = 64  # Procesar 64 chunks a la vez

def get_conn():
    url = os.environ.get("DATABASE_URL") or RAILWAY_DB_URL
    print(f"🔌 Conectando a: {url.split('@')[1].split('/')[0]}...")
    return psycopg2.connect(url)

def encode_normalized(model, texts):
    """Genera embeddings CORRECTAMENTE normalizados"""
    embeddings = model.encode(
        texts, 
        normalize_embeddings=True,  # 🔑 CRÍTICO
        convert_to_numpy=True,
        show_progress_bar=False
    )
    return embeddings

def vector_to_pgvector(embedding):
    """Convierte numpy array a formato pgvector"""
    return '[' + ','.join(str(float(x)) for x in embedding) + ']'

print("╔══════════════════════════════════════════════════════════════╗")
print("║        REGENERAR EMBEDDINGS NORMALIZADOS (RÁPIDO)           ║")
print("╚══════════════════════════════════════════════════════════════╝")

print("\n📋 Este proceso va a:")
print("   1. Leer los 25,653 chunks existentes (NO los elimina)")
print("   2. Regenerar embeddings normalizados (norma = 1.0)")
print("   3. Actualizar en la base de datos")
print("   4. Reconstruir índice IVFFlat")
print(f"\n   ⏱️  Tiempo estimado: ~30-40 minutos")

response = input("\n¿Deseas continuar? (escribe 'SI' para confirmar): ")

if response.upper() != 'SI':
    print("\n❌ Operación cancelada")
    exit(0)

start_time = time.time()

try:
    # Cargar modelo
    print("\n📦 Cargando modelo: hiiamsid/sentence_similarity_spanish_es")
    model = SentenceTransformer("hiiamsid/sentence_similarity_spanish_es", trust_remote_code=True)
    
    # Obtener todos los chunks
    print("\n📚 Obteniendo chunks de la BD...")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT chunk_id, content 
                FROM document_chunks 
                ORDER BY chunk_id
            """)
            chunks = cur.fetchall()
    
    print(f"✅ {len(chunks)} chunks encontrados")
    
    # Procesar en batches
    print(f"\n⚙️  Regenerando embeddings en lotes de {BATCH_SIZE}...")
    total_updated = 0
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Batches", unit="batch"):
                batch = chunks[i:i + BATCH_SIZE]
                
                # Extraer IDs y contenidos
                chunk_ids = [c[0] for c in batch]
                contents = [c[1] for c in batch]
                
                # Generar embeddings normalizados
                embeddings = encode_normalized(model, contents)
                
                # Actualizar en BD
                for chunk_id, embedding in zip(chunk_ids, embeddings):
                    embedding_str = vector_to_pgvector(embedding)
                    cur.execute("""
                        UPDATE document_chunks 
                        SET embedding = %s::vector 
                        WHERE chunk_id = %s
                    """, (embedding_str, chunk_id))
                
                total_updated += len(batch)
                
                # Commit cada 10 batches
                if (i // BATCH_SIZE) % 10 == 0:
                    conn.commit()
            
            # Commit final
            conn.commit()
    
    print(f"\n✅ {total_updated} embeddings actualizados")
    
    # Reconstruir índice
    print("\n🔧 Reconstruyendo índice IVFFlat...")
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Eliminar índice antiguo
            cur.execute("DROP INDEX IF EXISTS idx_document_chunks_vec")
            
            # Calcular listas óptimas
            cur.execute("SELECT COUNT(*) FROM document_chunks")
            total_chunks = cur.fetchone()[0]
            lists = max(10, int(total_chunks ** 0.5))
            
            print(f"   Creando índice con {lists} listas...")
            cur.execute(f"""
                CREATE INDEX idx_document_chunks_vec 
                ON document_chunks 
                USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = {lists})
            """)
            conn.commit()
    
    print("✅ Índice reconstruido")
    
    # Verificación rápida
    print("\n🔍 Verificando normalización...")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT embedding 
                FROM document_chunks 
                ORDER BY RANDOM() 
                LIMIT 10
            """)
            sample_embeddings = [row[0] for row in cur.fetchall()]
    
    # Calcular normas
    norms = []
    for emb_str in sample_embeddings:
        emb = np.array([float(x) for x in emb_str.strip('[]').split(',')])
        norm = np.linalg.norm(emb)
        norms.append(norm)
    
    avg_norm = np.mean(norms)
    print(f"   Norma promedio (muestra de 10): {avg_norm:.4f}")
    
    if 0.99 <= avg_norm <= 1.01:
        print("   ✅ Embeddings correctamente normalizados!")
    else:
        print(f"   ⚠️  Norma inesperada: {avg_norm:.4f} (esperado: ~1.0)")
    
    elapsed = time.time() - start_time
    print(f"\n🎉 ¡Proceso completado en {elapsed/60:.1f} minutos!")
    print("\n💡 Ejecuta 'python diagnostico_embeddings.py' para verificar mejoras")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
