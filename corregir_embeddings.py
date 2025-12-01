"""
Script de Corrección de Embeddings y Re-chunking
================================================

Corrige 3 problemas críticos:
1. Embeddings NO normalizados (actual: 1.5, esperado: 1.0)
2. Chunks demasiado largos (actual: 2785 chars, óptimo: 500 chars)
3. Búsqueda vectorial inferior a búsqueda de texto

Proceso:
1. Backup de datos actuales
2. Re-chunking con tamaño óptimo (500 chars, overlap 50)
3. Generación de embeddings normalizados
4. Reconstrucción de índice IVFFlat
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
from tqdm import tqdm
import time
import uuid

load_dotenv()

# Configuración
CHUNK_SIZE = 500  # Tamaño óptimo basado en investigación
CHUNK_OVERLAP = 50  # 10% de overlap
BATCH_SIZE = 32  # Procesar embeddings en lotes

# URL de Railway - Actualiza esto si cambia
RAILWAY_DB_URL = "postgres://postgres:wYmPtyJn8HbVZPpMC.ghW8InX-DaMyoS@switchyard.proxy.rlwy.net:32780/railway"

def get_conn():
    url = os.environ.get("DATABASE_URL") or RAILWAY_DB_URL
    if not url:
        raise RuntimeError("DATABASE_URL no configurada")
    print(f"🔌 Conectando a: {url.split('@')[1].split('/')[0]}...")  # Solo muestra el host
    return psycopg2.connect(url)

def get_model():
    name = os.environ.get("EMBEDDING_MODEL", "hiiamsid/sentence_similarity_spanish_es")
    print(f"📦 Cargando modelo: {name}")
    return SentenceTransformer(name, trust_remote_code=True)

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Divide texto en chunks con overlap"""
    if not text or len(text.strip()) == 0:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        # Tomar chunk_size caracteres
        end = start + chunk_size
        
        # Si no es el último chunk, buscar el último espacio para no cortar palabras
        if end < text_len:
            # Buscar último espacio en los últimos 50 caracteres
            last_space = text.rfind(' ', end - 50, end)
            if last_space > start:
                end = last_space
        
        chunk = text[start:end].strip()
        
        if chunk:  # Solo agregar chunks no vacíos
            chunks.append(chunk)
        
        # Mover inicio con overlap
        start = end - overlap
        
        # Si el próximo chunk sería muy pequeño, incluirlo en este
        if text_len - start < chunk_size // 2:
            break
    
    return chunks

def encode_normalized(model, texts: list[str]) -> list[np.ndarray]:
    """Genera embeddings CORRECTAMENTE normalizados"""
    # normalize_embeddings=True asegura norma = 1.0
    embeddings = model.encode(
        texts, 
        normalize_embeddings=True,  # 🔑 CRÍTICO: Normalizar
        convert_to_numpy=True,
        show_progress_bar=False
    )
    
    # Verificar normalización
    norms = [np.linalg.norm(emb) for emb in embeddings]
    avg_norm = np.mean(norms)
    
    if not (0.99 <= avg_norm <= 1.01):
        print(f"⚠️  WARNING: Norma promedio = {avg_norm:.4f} (esperado: ~1.0)")
    
    return embeddings

def vector_to_pgvector(vec: np.ndarray) -> str:
    """Convierte numpy array a formato PostgreSQL vector"""
    return '[' + ','.join(str(float(x)) for x in vec) + ']'

def backup_current_chunks():
    """Crea backup de chunks actuales antes de eliminar"""
    print("\n📦 Creando backup de chunks actuales...")
    
    with get_conn() as conn, conn.cursor() as cur:
        # Crear tabla de backup si no existe
        cur.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks_backup_old AS 
            SELECT * FROM document_chunks
            WHERE 1=0
        """)
        
        # Insertar datos actuales
        cur.execute("""
            INSERT INTO document_chunks_backup_old 
            SELECT * FROM document_chunks
        """)
        
        cur.execute("SELECT COUNT(*) FROM document_chunks_backup_old")
        count = cur.fetchone()[0]
        
        conn.commit()
        print(f"✅ Backup creado: {count} chunks guardados en document_chunks_backup_old")

def get_documents_content():
    """Obtiene documentos que aún NO tienen chunks procesados"""
    print("\n📚 Obteniendo documentos de la BD...")
    
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Solo documentos que NO tienen chunks ya procesados
        cur.execute("""
            SELECT 
                d.document_id,
                d.title,
                d.project_id,
                d.file_content
            FROM documents d
            WHERE d.file_content IS NOT NULL AND d.file_content != ''
            AND NOT EXISTS (
                SELECT 1 FROM document_chunks dc 
                WHERE dc.document_id = d.document_id
            )
            ORDER BY d.document_id
        """)
        docs = cur.fetchall()
    
    print(f"✅ {len(docs)} documentos pendientes de procesar")
    return docs

def delete_old_chunks():
    """Verifica chunks existentes (NO elimina)"""
    print("\n📊 Verificando chunks existentes...")
    
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM document_chunks")
        existing_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT document_id) FROM document_chunks")
        docs_with_chunks = cur.fetchone()[0]
        
        print(f"✅ {existing_count} chunks existentes de {docs_with_chunks} documentos")

def process_documents_in_batches(docs, model):
    """Procesa documentos: chunking + embeddings"""
    print(f"\n⚙️  Procesando {len(docs)} documentos...")
    print(f"   Tamaño de chunk: {CHUNK_SIZE} caracteres")
    print(f"   Overlap: {CHUNK_OVERLAP} caracteres")
    
    total_chunks_created = 0
    total_docs_processed = 0
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            for doc in tqdm(docs, desc="Documentos", unit="doc"):
                doc_id = doc['document_id']
                project_id = doc['project_id']
                title = doc.get('title', 'Sin título')
                content = doc['file_content']
                
                # Convertir bytes a string si es necesario
                if isinstance(content, (bytes, memoryview)):
                    content = bytes(content).decode('utf-8', errors='ignore')
                
                # Limpiar caracteres nulos (0x00) que PostgreSQL no acepta
                content = content.replace('\x00', '')
                
                if not content or len(content.strip()) == 0:
                    continue
                
                # Dividir en chunks
                chunks = chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP)
                
                if not chunks:
                    continue
                
                # Generar embeddings en lotes
                for i in range(0, len(chunks), BATCH_SIZE):
                    batch_chunks = chunks[i:i + BATCH_SIZE]
                    batch_embeddings = encode_normalized(model, batch_chunks)
                    
                    # Insertar en BD
                    for chunk_idx, (chunk_content, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                        chunk_id = str(uuid.uuid4())  # Generar UUID válido
                        embedding_str = vector_to_pgvector(embedding)
                        
                        cur.execute("""
                            INSERT INTO document_chunks (
                                chunk_id, 
                                document_id, 
                                project_id, 
                                title,
                                content, 
                                embedding,
                                date_modified
                            ) VALUES (%s, %s, %s, %s, %s, %s::vector, NOW())
                        """, (
                            chunk_id,
                            doc_id,
                            project_id,
                            title,
                            chunk_content,
                            embedding_str
                        ))
                    
                    total_chunks_created += len(batch_chunks)
                
                total_docs_processed += 1
                
                # Commit cada 100 documentos
                if total_docs_processed % 100 == 0:
                    conn.commit()
            
            # Commit final
            conn.commit()
    
    print(f"\n✅ Procesamiento completado:")
    print(f"   Documentos: {total_docs_processed}")
    print(f"   Chunks creados: {total_chunks_created}")
    print(f"   Chunks/documento: {total_chunks_created/total_docs_processed:.1f}")

def rebuild_ivfflat_index():
    """Reconstruye el índice IVFFlat"""
    print("\n🔨 Reconstruyendo índice IVFFlat...")
    
    with get_conn() as conn, conn.cursor() as cur:
        # Eliminar índice antiguo
        print("   Eliminando índice antiguo...")
        cur.execute("DROP INDEX IF EXISTS idx_document_chunks_vec")
        
        # Calcular número óptimo de listas (clusters)
        cur.execute("SELECT COUNT(*) FROM document_chunks")
        chunk_count = cur.fetchone()[0]
        
        # Fórmula recomendada: sqrt(rows)
        lists = max(int(np.sqrt(chunk_count)), 10)
        
        print(f"   Creando índice con {lists} listas...")
        
        # Crear nuevo índice
        cur.execute(f"""
            CREATE INDEX idx_document_chunks_vec 
            ON document_chunks 
            USING ivfflat (embedding vector_cosine_ops) 
            WITH (lists = {lists})
        """)
        
        conn.commit()
        print(f"✅ Índice reconstruido con {lists} listas")

def verify_results():
    """Verifica que los embeddings estén correctos"""
    print("\n🔍 Verificando resultados...")
    
    model = get_model()
    
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Verificar normalización
        cur.execute("""
            SELECT embedding::text 
            FROM document_chunks 
            LIMIT 100
        """)
        rows = cur.fetchall()
        
        norms = []
        for row in rows:
            emb_str = row['embedding']
            emb_values = [float(x) for x in emb_str.strip('[]').split(',')]
            emb_array = np.array(emb_values)
            norm = np.linalg.norm(emb_array)
            norms.append(norm)
        
        avg_norm = np.mean(norms)
        std_norm = np.std(norms)
        
        print(f"\n📊 Análisis de normalización:")
        print(f"   Promedio: {avg_norm:.4f} (esperado: ~1.0)")
        print(f"   Desv. Est: {std_norm:.4f} (esperado: ~0.0)")
        
        if 0.99 <= avg_norm <= 1.01:
            print("   ✅ Embeddings correctamente normalizados")
        else:
            print(f"   ❌ Embeddings NO normalizados")
        
        # Verificar longitud de chunks
        cur.execute("""
            SELECT 
                AVG(LENGTH(content)) as avg_len,
                MIN(LENGTH(content)) as min_len,
                MAX(LENGTH(content)) as max_len
            FROM document_chunks
        """)
        stats = cur.fetchone()
        
        print(f"\n📏 Estadísticas de chunks:")
        print(f"   Promedio: {stats['avg_len']:.0f} chars")
        print(f"   Mínimo: {stats['min_len']} chars")
        print(f"   Máximo: {stats['max_len']} chars")
        
        if 400 <= stats['avg_len'] <= 600:
            print("   ✅ Longitud de chunks en rango óptimo")
        else:
            print(f"   ⚠️  Longitud promedio fuera del rango óptimo (400-600)")
        
        # Test de búsqueda
        print(f"\n🔍 Test de búsqueda: 'informe de costos'")
        
        query_emb = encode_normalized(model, ["informe de costos"])[0]
        query_str = vector_to_pgvector(query_emb)
        
        cur.execute(f"""
            SELECT 
                d.title,
                dc.content,
                1 - (dc.embedding <=> '{query_str}') AS similarity
            FROM document_chunks dc
            JOIN documents d ON d.document_id = dc.document_id
            ORDER BY dc.embedding <=> '{query_str}'
            LIMIT 5
        """)
        results = cur.fetchall()
        
        print(f"\n   Top 5 resultados:")
        for i, row in enumerate(results, 1):
            sim = row['similarity']
            title = row['title'][:50] + "..." if len(row['title']) > 50 else row['title']
            
            if sim >= 0.7:
                quality = "EXCELENTE ✅"
            elif sim >= 0.5:
                quality = "BUENO ✅"
            elif sim >= 0.4:
                quality = "MODERADO ⚠️"
            else:
                quality = "BAJO ❌"
            
            print(f"   {i}. [{sim:.3f} - {quality}] {title}")
        
        best_sim = results[0]['similarity']
        
        if best_sim >= 0.6:
            print(f"\n   ✅ Búsqueda vectorial funcionando correctamente")
        elif best_sim >= 0.4:
            print(f"\n   ⚠️  Búsqueda vectorial mejoró pero aún puede optimizarse")
        else:
            print(f"\n   ❌ Búsqueda vectorial aún tiene problemas")

def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                              ║")
    print("║           CORRECCIÓN DE EMBEDDINGS - MODO INCREMENTAL                        ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    
    print("\n📋 Este proceso va a:")
    print("   1. Crear backup de chunks actuales (si no existe)")
    print("   2. Procesar SOLO documentos sin chunks")
    print("   3. Generar embeddings normalizados (norma = 1.0)")
    print("   4. Reconstruir el índice IVFFlat al final")
    print("\n   ✨ Los chunks ya procesados NO se eliminarán")
    
    response = input("\n¿Deseas continuar? (escribe 'SI' para confirmar): ")
    
    if response.upper() != 'SI':
        print("\n❌ Operación cancelada")
        return
    
    start_time = time.time()
    
    try:
        # Paso 1: Verificar/Crear Backup solo si no existe
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'document_chunks_backup_old'
                )
            """)
            backup_exists = cur.fetchone()[0]
        
        if not backup_exists:
            print("\n📦 Creando backup por primera vez...")
            backup_current_chunks()
        else:
            print("\n✅ Backup ya existe: document_chunks_backup_old")
        
        # Paso 2: Cargar modelo
        model = get_model()
        
        # Paso 3: Verificar chunks existentes (NO eliminar)
        delete_old_chunks()
        
        # Paso 4: Obtener solo documentos sin chunks
        docs = get_documents_content()
        
        if not docs:
            print("\n🎉 ¡Todos los documentos ya tienen chunks procesados!")
            print("   Reconstruyendo índice IVFFlat...")
            rebuild_ivfflat_index()
            return
        
        # Paso 5: Procesar solo documentos faltantes
        process_documents_in_batches(docs, model)
        
        # Paso 6: Reconstruir índice
        rebuild_ivfflat_index()
        
        # Paso 7: Verificar resultados
        verify_results()
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*80)
        print(f"✅ PROCESO COMPLETADO EXITOSAMENTE")
        print(f"⏱️  Tiempo total: {elapsed/60:.1f} minutos")
        print("="*80)
        
        print("\n📝 Próximos pasos:")
        print("   1. Ejecuta: python diagnostico_embeddings.py")
        print("   2. Verifica que las similitudes sean >= 0.5")
        print("   3. Prueba búsquedas en el frontend")
        
    except KeyboardInterrupt:
        print("\n\n❌ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n💡 Si hubo un error, puedes restaurar el backup:")
        print("   DELETE FROM document_chunks;")
        print("   INSERT INTO document_chunks SELECT * FROM document_chunks_backup_old;")

if __name__ == "__main__":
    main()
