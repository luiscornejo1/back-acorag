"""
Script para limpiar backup duplicados y restaurar
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

RAILWAY_DB_URL = "postgres://postgres:wYmPtyJn8HbVZPpMC.ghW8InX-DaMyoS@switchyard.proxy.rlwy.net:32780/railway"

def get_conn():
    url = os.environ.get("DATABASE_URL") or RAILWAY_DB_URL
    print(f"🔌 Conectando a: {url.split('@')[1].split('/')[0]}...")
    return psycopg2.connect(url)

print("╔══════════════════════════════════════════════════════════════╗")
print("║        LIMPIAR BACKUP DUPLICADOS Y RESTAURAR                 ║")
print("╚══════════════════════════════════════════════════════════════╝")

print("\n⚠️  Este proceso va a:")
print("   1. Limpiar chunks duplicados del backup")
print("   2. Restaurar solo chunks únicos")
print("   3. Preservar los documentos ya procesados correctamente")

response = input("\n¿Deseas continuar? (escribe 'SI' para confirmar): ")

if response.upper() != 'SI':
    print("\n❌ Operación cancelada")
    exit(0)

try:
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Ver estado del backup
            print("\n📦 Analizando backup...")
            cur.execute("SELECT COUNT(*) FROM document_chunks_backup_old")
            backup_total = cur.fetchone()[0]
            print(f"   Total en backup: {backup_total}")
            
            cur.execute("SELECT COUNT(DISTINCT chunk_id) FROM document_chunks_backup_old")
            backup_unique = cur.fetchone()[0]
            print(f"   Chunks únicos: {backup_unique}")
            print(f"   Duplicados: {backup_total - backup_unique}")
            
            # Limpiar backup - quedarse solo con los chunks más recientes por chunk_id
            print("\n🧹 Limpiando backup duplicados...")
            
            # Crear tabla temporal con chunks únicos
            cur.execute("""
                CREATE TEMP TABLE backup_limpio AS
                SELECT DISTINCT ON (chunk_id) *
                FROM document_chunks_backup_old
                ORDER BY chunk_id, date_modified DESC
            """)
            
            cur.execute("SELECT COUNT(*) FROM backup_limpio")
            backup_clean = cur.fetchone()[0]
            print(f"✅ {backup_clean} chunks únicos identificados")
            
            # Vaciar tabla actual completamente
            print("\n🗑️  Vaciando tabla document_chunks...")
            cur.execute("TRUNCATE TABLE document_chunks RESTART IDENTITY CASCADE")
            conn.commit()
            print("✅ Tabla vaciada")
            
            # Restaurar desde tabla limpia
            print("\n♻️  Restaurando backup limpio...")
            cur.execute("INSERT INTO document_chunks SELECT * FROM backup_limpio")
            conn.commit()
            
            # Verificar restauración
            cur.execute("SELECT COUNT(*) FROM document_chunks")
            restored_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(DISTINCT document_id) FROM document_chunks")
            docs_restored = cur.fetchone()[0]
            
            print(f"✅ {restored_count} chunks restaurados")
            print(f"✅ {docs_restored} documentos con chunks")
            
            # Mostrar documentos faltantes
            cur.execute("""
                SELECT COUNT(*) 
                FROM documents 
                WHERE file_content IS NOT NULL 
                AND NOT EXISTS (
                    SELECT 1 FROM document_chunks 
                    WHERE document_chunks.document_id = documents.document_id
                )
            """)
            pending = cur.fetchone()[0]
            
            print(f"\n📊 Resumen:")
            print(f"   ✅ Documentos procesados: {docs_restored}")
            print(f"   ⏳ Documentos pendientes: {pending}")
            print(f"   📦 Total chunks: {restored_count}")
            
            print("\n🎉 ¡Backup restaurado exitosamente!")
            print(f"\n💡 Ahora ejecuta: python corregir_embeddings.py")
            print(f"   Solo procesará los {pending} documentos faltantes en ~2-3 minutos")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
