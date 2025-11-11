"""
Script para verificar qué datos hay actualmente en la base de datos
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 VERIFICACIÓN DE BASE DE DATOS ACTUAL")
print("="*70)

try:
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    cur = conn.cursor()
    
    # 1. Contar documentos totales
    cur.execute("SELECT COUNT(*) FROM documents")
    total_docs = cur.fetchone()[0]
    print(f"\n📊 DOCUMENTOS EN BD: {total_docs:,}")
    
    # 2. Contar chunks totales
    cur.execute("SELECT COUNT(*) FROM document_chunks")
    total_chunks = cur.fetchone()[0]
    print(f"📊 CHUNKS EN BD: {total_chunks:,}")
    
    # 3. Verificar si hay contenido sintético (largo)
    cur.execute("""
        SELECT 
            chunk_id,
            LENGTH(content) as longitud,
            LEFT(content, 100) as preview
        FROM document_chunks 
        LIMIT 5
    """)
    
    print(f"\n📝 MUESTRA DE CHUNKS (primeros 5):")
    print("-"*70)
    
    chunks = cur.fetchall()
    for i, (chunk_id, longitud, preview) in enumerate(chunks, 1):
        print(f"\n{i}. Chunk ID: {chunk_id}")
        print(f"   Longitud: {longitud} caracteres")
        print(f"   Preview: {preview}...")
        
        # Detectar si es metadata-only o contenido sintético
        if longitud < 200:
            print(f"   ⚠️  METADATA-ONLY (muy corto)")
        elif longitud > 1000:
            print(f"   ✅ CONTENIDO RICO (posible sintético)")
        else:
            print(f"   ⚡ CONTENIDO MEDIO")
    
    # 4. Estadísticas de longitud
    cur.execute("""
        SELECT 
            AVG(LENGTH(content)) as promedio,
            MIN(LENGTH(content)) as minimo,
            MAX(LENGTH(content)) as maximo
        FROM document_chunks
    """)
    
    promedio, minimo, maximo = cur.fetchone()
    
    print(f"\n📈 ESTADÍSTICAS DE LONGITUD DE CHUNKS:")
    print(f"   Mínimo: {minimo} caracteres")
    print(f"   Promedio: {promedio:.0f} caracteres")
    print(f"   Máximo: {maximo} caracteres")
    
    # 5. Verificar project_id
    cur.execute("""
        SELECT DISTINCT project_id, COUNT(*) 
        FROM documents 
        GROUP BY project_id
    """)
    
    print(f"\n🏷️  PROYECTOS EN BD:")
    projects = cur.fetchall()
    for project_id, count in projects:
        print(f"   - {project_id}: {count:,} documentos")
    
    # 6. DIAGNÓSTICO
    print(f"\n" + "="*70)
    print("🔬 DIAGNÓSTICO:")
    print("="*70)
    
    if total_docs > 100000:
        print("❌ Tienes la BD VIEJA con 147K documentos metadata-only")
        print("   → Necesitas ejecutar: python limpiar_todo_force.py")
    elif total_docs < 5000 and promedio > 1000:
        print("✅ Tienes contenido SINTÉTICO (chunks largos)")
        print("   → Los scores deberían ser 0.6-0.8")
    elif total_docs < 5000 and promedio < 500:
        print("⚠️  Tienes pocos docs pero chunks CORTOS (metadata-only)")
        print("   → Verifica que hayas ingresado el JSON correcto")
    else:
        print("❓ Situación no clara. Revisa los datos arriba.")
    
    print("="*70)
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
