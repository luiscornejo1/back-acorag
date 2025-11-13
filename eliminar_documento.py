"""
Script para eliminar un documento específico de la base de datos
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()

def eliminar_documento(titulo_buscar):
    """Elimina un documento y todos sus chunks de la BD"""
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("❌ ERROR: DATABASE_URL no configurada")
        return
    
    conn = psycopg2.connect(url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Buscar documento
        cur.execute("""
            SELECT document_id, title, filename,
                   (SELECT COUNT(*) FROM document_chunks WHERE document_id = d.document_id) as num_chunks
            FROM documents d
            WHERE LOWER(title) LIKE LOWER(%s) OR LOWER(filename) LIKE LOWER(%s)
            ORDER BY date_modified DESC
            LIMIT 5
        """, (f'%{titulo_buscar}%', f'%{titulo_buscar}%'))
        
        docs = cur.fetchall()
        
        if not docs:
            print(f"❌ No se encontró documento con '{titulo_buscar}'")
            return
        
        if len(docs) > 1:
            print(f"\n📄 Se encontraron {len(docs)} documentos:")
            for i, doc in enumerate(docs, 1):
                print(f"\n{i}. {doc['title']}")
                print(f"   ID: {doc['document_id'][:30]}...")
                print(f"   Archivo: {doc['filename']}")
                print(f"   Chunks: {doc['num_chunks']}")
            
            print("\n¿Cuál quieres eliminar? (número 1-5, o 'todos' para eliminar todos)")
            opcion = input("> ").strip().lower()
            
            if opcion == 'todos':
                docs_a_eliminar = docs
            else:
                try:
                    idx = int(opcion) - 1
                    if 0 <= idx < len(docs):
                        docs_a_eliminar = [docs[idx]]
                    else:
                        print("❌ Número inválido")
                        return
                except ValueError:
                    print("❌ Opción inválida")
                    return
        else:
            docs_a_eliminar = docs
        
        # Confirmar eliminación
        print(f"\n⚠️  VAS A ELIMINAR {len(docs_a_eliminar)} documento(s):")
        for doc in docs_a_eliminar:
            print(f"   - {doc['title']} ({doc['num_chunks']} chunks)")
        
        print("\n¿Estás seguro? (escribe 'SI' para confirmar):")
        confirmacion = input("> ").strip().upper()
        
        if confirmacion != "SI":
            print("❌ Operación cancelada")
            return
        
        # Eliminar documentos
        total_chunks = 0
        for doc in docs_a_eliminar:
            doc_id = doc['document_id']
            
            # Eliminar chunks
            cur.execute("DELETE FROM document_chunks WHERE document_id = %s", (doc_id,))
            chunks_eliminados = cur.rowcount
            total_chunks += chunks_eliminados
            
            # Eliminar documento
            cur.execute("DELETE FROM documents WHERE document_id = %s", (doc_id,))
            
            print(f"✅ Eliminado: {doc['title']} ({chunks_eliminados} chunks)")
        
        conn.commit()
        
        print(f"\n🎉 ¡Completado!")
        print(f"   Documentos eliminados: {len(docs_a_eliminar)}")
        print(f"   Chunks eliminados: {total_chunks}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("🗑️  ELIMINAR DOCUMENTO")
    print("=" * 100)
    print("\nEscribe parte del título o nombre del archivo a eliminar:")
    titulo = input("> ").strip()
    
    if titulo:
        eliminar_documento(titulo)
    else:
        print("❌ No ingresaste ningún término de búsqueda")
