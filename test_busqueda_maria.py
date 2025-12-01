"""
Test de búsqueda: "tesis sobre aplicaciones moviles de maria hoyos"
"""
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

RAILWAY_DB_URL = "postgres://postgres:wYmPtyJn8HbVZPpMC.ghW8InX-DaMyoS@switchyard.proxy.rlwy.net:32780/railway"

def get_conn():
    url = os.environ.get("DATABASE_URL") or RAILWAY_DB_URL
    return psycopg2.connect(url)

# Cargar modelo
print("📦 Cargando modelo...")
model = SentenceTransformer("hiiamsid/sentence_similarity_spanish_es", trust_remote_code=True)

# Query
query = "tesis sobre aplicaciones moviles de maria hoyos"
print(f"\n🔍 Query: '{query}'")

# Generar embedding
embedding = model.encode([query], normalize_embeddings=True, convert_to_numpy=True)[0]
embedding_str = '[' + ','.join(str(float(x)) for x in embedding) + ']'

# Buscar
with get_conn() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""
            SELECT 
                d.document_id,
                d.title,
                (1 - (dc.embedding <=> '{embedding_str}')) AS vector_score,
                ts_rank(to_tsvector('spanish', COALESCE(d.title, '')), plainto_tsquery('spanish', '{query}')) * 2.0 AS text_score,
                (1 - (dc.embedding <=> '{embedding_str}')) * 0.6 + 
                ts_rank(to_tsvector('spanish', COALESCE(d.title, '')), plainto_tsquery('spanish', '{query}')) * 2.0 * 0.4 AS combined_score
            FROM document_chunks dc
            JOIN documents d ON d.document_id = dc.document_id
            WHERE d.title ILIKE '%maria%' OR d.title ILIKE '%hoyos%'
            ORDER BY combined_score DESC
            LIMIT 5
        """)
        
        results = cur.fetchall()

print(f"\n📊 Resultados para documento de Maria Hoyos:\n")
for i, r in enumerate(results, 1):
    print(f"{i}. {r['title']}")
    print(f"   Vector Score: {r['vector_score']:.4f}")
    print(f"   Text Score: {r['text_score']:.4f}")
    print(f"   Combined Score: {r['combined_score']:.4f}")
    print()

if results and results[0]['combined_score'] >= 0.65:
    print("✅ MODO ESTRICTO: SÍ aparecería (score >= 0.65)")
elif results and results[0]['combined_score'] >= 0.35:
    print("✅ MODO ADAPTATIVO: SÍ aparecería (score >= 0.35)")
else:
    print("❌ NO aparecería con los thresholds actuales")

print(f"\n💡 Con esta búsqueda específica, el score debería ser ALTO porque:")
print("   - Menciona 'maria hoyos' (match en título)")
print("   - Menciona 'aplicaciones moviles' (match en título)")
print("   - Menciona 'tesis' (contexto académico)")
