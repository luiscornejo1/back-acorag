"""
Script para verificar qué documentos están en la base de datos
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

def verificar_documentos():
    """Muestra todos los documentos en la BD con detalles"""
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("❌ ERROR: DATABASE_URL no configurada")
        return
    
    conn = psycopg2.connect(url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Contar documentos totales
        cur.execute("SELECT COUNT(*) as total FROM documents")
        total = cur.fetchone()['total']
        print(f"📊 Total de documentos en BD: {total}\n")
        
        # Obtener documentos recientes (últimos 20)
        cur.execute("""
            SELECT 
                document_id,
                title,
                filename,
                file_type,
                date_modified,
                (SELECT COUNT(*) FROM document_chunks WHERE document_id = d.document_id) as num_chunks
            FROM documents d
            ORDER BY date_modified DESC
            LIMIT 20
        """)
        
        docs = cur.fetchall()
        
        print("📄 ÚLTIMOS 20 DOCUMENTOS (más recientes primero):")
        print("=" * 100)
        
        for i, doc in enumerate(docs, 1):
            doc_id = doc['document_id'][:20] + "..."
            title = doc['title'][:50] if doc['title'] else 'Sin título'
            filename = doc['filename'][:40] if doc['filename'] else 'N/A'
            chunks = doc['num_chunks']
            fecha = doc['date_modified'].strftime('%Y-%m-%d %H:%M') if doc['date_modified'] else 'N/A'
            
            print(f"\n{i}. {title}")
            print(f"   📁 Archivo: {filename}")
            print(f"   🆔 ID: {doc_id}")
            print(f"   📝 Chunks: {chunks}")
            print(f"   📅 Fecha: {fecha}")
        
        print("\n" + "=" * 100)
        
        # Buscar documentos específicos por nombre
        print("\n🔍 ¿Quieres buscar un documento específico?")
        print("Escribe parte del título o nombre de archivo (o Enter para salir):")
        
        buscar = input("> ").strip()
        
        if buscar:
            cur.execute("""
                SELECT 
                    document_id,
                    title,
                    filename,
                    file_type,
                    date_modified,
                    (SELECT COUNT(*) FROM document_chunks WHERE document_id = d.document_id) as num_chunks
                FROM documents d
                WHERE 
                    LOWER(title) LIKE LOWER(%s) OR
                    LOWER(filename) LIKE LOWER(%s)
                ORDER BY date_modified DESC
            """, (f'%{buscar}%', f'%{buscar}%'))
            
            resultados = cur.fetchall()
            
            if resultados:
                print(f"\n✅ Encontrados {len(resultados)} documentos:")
                for doc in resultados:
                    print(f"\n📄 {doc['title']}")
                    print(f"   Archivo: {doc['filename']}")
                    print(f"   Chunks: {doc['num_chunks']}")
                    print(f"   Fecha: {doc['date_modified']}")
            else:
                print(f"\n❌ No se encontraron documentos con '{buscar}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    verificar_documentos()
