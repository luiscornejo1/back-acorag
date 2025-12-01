"""
Script para restaurar el backup de chunks
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
print("║      RESTAURAR BACKUP DE CHUNKS (1667 docs procesados)      ║")
print("╚══════════════════════════════════════════════════════════════╝")

print("\n⚠️  Este proceso va a:")
print("   1. Eliminar chunks actuales")
print("   2. Restaurar 20,663 chunks del backup")
print("   3. Ahora solo faltarán ~15 documentos por procesar")

response = input("\n¿Deseas continuar? (escribe 'SI' para confirmar): ")

if response.upper() != 'SI':
    print("\n❌ Operación cancelada")
    exit(0)

try:
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Verificar backup
            print("\n📦 Verificando backup...")
            cur.execute("SELECT COUNT(*) FROM document_chunks_backup_old")
            backup_count = cur.fetchone()[0]
            print(f"✅ Backup encontrado: {backup_count} chunks")
            
            if backup_count == 0:
                print("❌ El backup está vacío")
                exit(1)
            
            # Eliminar chunks actuales
            print("\n🗑️  Eliminando chunks actuales...")
            cur.execute("SELECT COUNT(*) FROM document_chunks")
            current_count = cur.fetchone()[0]
            print(f"   Chunks actuales: {current_count}")
            
            cur.execute("TRUNCATE TABLE document_chunks")
            conn.commit()
            print("✅ Chunks eliminados")
            
            # Restaurar backup
            print("\n♻️  Restaurando backup...")
            cur.execute("INSERT INTO document_chunks SELECT * FROM document_chunks_backup_old")
            conn.commit()
            
            # Verificar
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
            print("\n💡 Ahora ejecuta: python corregir_embeddings.py")
            print("   Solo procesará los {pending} documentos faltantes")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
