"""
Script para limpiar completamente la base de datos y empezar de cero
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def limpiar_database():
    """Elimina TODOS los documentos y chunks para empezar de cero"""
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("❌ ERROR: DATABASE_URL no configurada")
        return
    
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    try:
        print("🗑️  Limpiando base de datos...")
        
        # Eliminar todos los chunks
        cur.execute("DELETE FROM document_chunks")
        chunks_deleted = cur.rowcount
        print(f"   ✅ {chunks_deleted} chunks eliminados")
        
        # Eliminar todos los documentos
        cur.execute("DELETE FROM documents")
        docs_deleted = cur.rowcount
        print(f"   ✅ {docs_deleted} documentos eliminados")
        
        # Commit
        conn.commit()
        
        print("\n✨ Base de datos limpiada exitosamente!")
        print("📝 Ahora puedes subir tus documentos nuevamente desde el frontend")
        print("   Todos usarán el modelo: hiiamsid/sentence_similarity_spanish_es")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("⚠️  ADVERTENCIA: Esto eliminará TODOS los documentos de la base de datos")
    respuesta = input("¿Estás seguro? (escribe 'SI' para continuar): ")
    
    if respuesta.strip().upper() == "SI":
        limpiar_database()
    else:
        print("❌ Operación cancelada")
