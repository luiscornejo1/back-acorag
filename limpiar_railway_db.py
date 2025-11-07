"""
Script para limpiar tablas en Railway y permitir re-ingesta con nuevo modelo
"""
import psycopg2
import os

print("🔧 Conectando a base de datos de Railway...")

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

print("🗑️  Eliminando tablas antiguas...")

try:
    # Eliminar tablas en orden correcto (chunks primero por foreign key)
    cur.execute("DROP TABLE IF EXISTS chunks CASCADE")
    print("  ✅ Tabla 'chunks' eliminada")
    
    cur.execute("DROP TABLE IF EXISTS documents CASCADE")
    print("  ✅ Tabla 'documents' eliminada")
    
    cur.execute("DROP TABLE IF EXISTS chat_feedback CASCADE")
    print("  ✅ Tabla 'chat_feedback' eliminada")
    
    cur.execute("DROP TABLE IF EXISTS search_logs CASCADE")
    print("  ✅ Tabla 'search_logs' eliminada")
    
    cur.execute("DROP TABLE IF EXISTS chat_history CASCADE")
    print("  ✅ Tabla 'chat_history' eliminada")
    
    # Eliminar y recrear extensión pgvector para limpiar índices
    print("\n🔄 Recreando extensión pgvector...")
    cur.execute("DROP EXTENSION IF EXISTS vector CASCADE")
    print("  ✅ Extensión 'vector' eliminada")
    
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    print("  ✅ Extensión 'vector' recreada")
    
    conn.commit()
    print("\n✅ Todas las tablas y extensiones limpiadas correctamente")
    print("\n📝 Ahora puedes ejecutar:")
    print("   railway run python -m app.ingest --json_path data/mis_correos_optimizado.json --project_id default")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    conn.rollback()

finally:
    cur.close()
    conn.close()
