"""
Script para FORZAR limpieza COMPLETA de la base de datos
"""
import psycopg2
import os

print("🔧 LIMPIEZA TOTAL DE BASE DE DATOS")
print("="*60)

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
conn.autocommit = True  # Importante para DROP
cur = conn.cursor()

try:
    # Eliminar TODAS las tablas relacionadas
    print("🗑️  Eliminando TODAS las tablas...")
    
    cur.execute("DROP TABLE IF EXISTS chunks CASCADE")
    cur.execute("DROP TABLE IF EXISTS document_chunks CASCADE")
    cur.execute("DROP TABLE IF EXISTS documents CASCADE")
    cur.execute("DROP TABLE IF EXISTS chat_feedback CASCADE")
    cur.execute("DROP TABLE IF EXISTS search_logs CASCADE")
    cur.execute("DROP TABLE IF EXISTS chat_history CASCADE")
    
    print("✅ Todas las tablas eliminadas")
    
    # Eliminar extensión vector
    print("\n🔄 Recreando extensión vector...")
    cur.execute("DROP EXTENSION IF EXISTS vector CASCADE")
    cur.execute("CREATE EXTENSION vector")
    print("✅ Extensión vector recreada")
    
    # Verificar que no queden tablas
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    remaining = cur.fetchall()
    
    print("\n📋 Tablas restantes:")
    if remaining:
        for t in remaining:
            print(f"  - {t[0]}")
    else:
        print("  ✅ NINGUNA - Base de datos limpia")
    
    print("\n" + "="*60)
    print("✅ LIMPIEZA COMPLETADA")
    print("="*60)
    print("\n💡 Ahora ejecuta:")
    print("   python -m app.ingest --json_path data/mis_correos_optimizado.json --project_id ACONEX")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    cur.close()
    conn.close()
