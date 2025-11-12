"""
Script para migrar la columna 'raw' de jsonb a bytea en la tabla documents
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL no está configurada en .env")

print("🔧 Conectando a la base de datos...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

try:
    # Paso 1: Verificar tipo actual de la columna raw
    cur.execute("""
        SELECT data_type 
        FROM information_schema.columns 
        WHERE table_name = 'documents' AND column_name = 'raw'
    """)
    current_type = cur.fetchone()
    
    if current_type:
        print(f"📊 Tipo actual de columna 'raw': {current_type[0]}")
        
        if current_type[0] == 'jsonb':
            print("🔄 Migrando columna 'raw' de jsonb a bytea...")
            
            # Paso 2: Eliminar la columna raw (si tiene datos importantes, hacer backup primero)
            cur.execute("ALTER TABLE documents DROP COLUMN IF EXISTS raw")
            print("  ✅ Columna 'raw' eliminada")
            
            # Paso 3: Recrear la columna como bytea
            cur.execute("ALTER TABLE documents ADD COLUMN raw bytea")
            print("  ✅ Columna 'raw' recreada como bytea")
            
            conn.commit()
            print("✅ Migración completada exitosamente!")
            print("\n🎯 Ahora ejecuta: python cargar_pdfs_a_bd.py")
            
        elif current_type[0] == 'bytea':
            print("✅ La columna 'raw' ya es de tipo bytea. No se necesita migración.")
        else:
            print(f"⚠️ Tipo de columna inesperado: {current_type[0]}")
    else:
        print("⚠️ La columna 'raw' no existe. Creándola...")
        cur.execute("ALTER TABLE documents ADD COLUMN raw bytea")
        conn.commit()
        print("✅ Columna 'raw' creada como bytea")

except Exception as e:
    print(f"❌ Error durante la migración: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
    print("🔌 Conexión cerrada")
