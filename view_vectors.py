#!/usr/bin/env python3
"""
Script para visualizar todos los vectores en la base de datos
"""
import psycopg2
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no configurada")
    return psycopg2.connect(url)

def view_all_vectors(limit=50, offset=0, show_full_vector=False):
    """Ver todos los vectores con paginación"""
    conn = get_conn()
    cur = conn.cursor()
    
    # Contar total
    cur.execute("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
    total = cur.fetchone()[0]
    
    print(f"=== VECTORES EN BASE DE DATOS ===")
    print(f"Total vectores: {total:,}")
    print(f"Mostrando del {offset+1} al {min(offset+limit, total)}")
    print("=" * 60)
    
    # Obtener vectores
    vector_preview = "embedding::text" if show_full_vector else "SUBSTRING(embedding::text, 1, 100) as vector_preview"
    
    cur.execute(f"""
        SELECT document_id, title, project_id,
               SUBSTRING(content, 1, 100) as content_preview,
               {vector_preview}
        FROM document_chunks 
        WHERE embedding IS NOT NULL 
        ORDER BY document_id
        LIMIT %s OFFSET %s
    """, (limit, offset))
    
    for i, row in enumerate(cur.fetchall(), offset+1):
        print(f"\n--- VECTOR {i} ---")
        print(f"Doc ID: {row[0]}")
        print(f"Título: {row[1][:60]}..." if row[1] else "Sin título")
        print(f"Proyecto: {row[2] or 'Sin proyecto'}")
        print(f"Contenido: {row[3]}...")
        if show_full_vector:
            print(f"Vector completo: {row[4]}")
        else:
            print(f"Vector (preview): {row[4]}...")
        print("-" * 40)
    
    cur.close()
    conn.close()
    
    return total

def view_vectors_by_project(project_id=None):
    """Ver vectores filtrados por proyecto"""
    conn = get_conn()
    cur = conn.cursor()
    
    if project_id:
        where_clause = "WHERE embedding IS NOT NULL AND project_id = %s"
        params = (project_id,)
        title = f"VECTORES DEL PROYECTO: {project_id}"
    else:
        where_clause = "WHERE embedding IS NOT NULL"
        params = ()
        title = "VECTORES POR PROYECTO"
    
    print(f"=== {title} ===")
    
    # Contar por proyecto
    cur.execute(f"""
        SELECT project_id, COUNT(*) as count
        FROM document_chunks 
        {where_clause}
        GROUP BY project_id
        ORDER BY count DESC
    """, params)
    
    projects = cur.fetchall()
    for proj, count in projects:
        print(f"{proj or 'Sin proyecto'}: {count:,} vectores")
    
    if project_id:
        print(f"\n=== DOCUMENTOS EN {project_id} ===")
        cur.execute(f"""
            SELECT document_id, title,
                   SUBSTRING(content, 1, 80) as content_preview,
                   SUBSTRING(embedding::text, 1, 80) as vector_preview
            FROM document_chunks 
            WHERE embedding IS NOT NULL AND project_id = %s
            ORDER BY document_id
            LIMIT 20
        """, (project_id,))
        
        for row in cur.fetchall():
            print(f"\nDoc: {row[0]}")
            print(f"Título: {row[1][:50]}..." if row[1] else "Sin título")
            print(f"Contenido: {row[2]}...")
            print(f"Vector: {row[3]}...")
    
    cur.close()
    conn.close()

def search_vectors_by_content(search_term):
    """Buscar vectores por contenido"""
    conn = get_conn()
    cur = conn.cursor()
    
    print(f"=== BÚSQUEDA: '{search_term}' ===")
    
    cur.execute("""
        SELECT document_id, title, project_id,
               content,
               SUBSTRING(embedding::text, 1, 100) as vector_preview
        FROM document_chunks 
        WHERE embedding IS NOT NULL 
        AND (LOWER(content) LIKE LOWER(%s) OR LOWER(title) LIKE LOWER(%s))
        ORDER BY document_id
        LIMIT 20
    """, (f"%{search_term}%", f"%{search_term}%"))
    
    results = cur.fetchall()
    print(f"Encontrados: {len(results)} vectores")
    
    for i, row in enumerate(results, 1):
        print(f"\n--- RESULTADO {i} ---")
        print(f"Doc ID: {row[0]}")
        print(f"Título: {row[1][:60]}..." if row[1] else "Sin título")
        print(f"Proyecto: {row[2] or 'Sin proyecto'}")
        print(f"Contenido: {row[3][:200]}...")
        print(f"Vector: {row[4]}...")
    
    cur.close()
    conn.close()

def vector_stats():
    """Estadísticas de vectores"""
    conn = get_conn()
    cur = conn.cursor()
    
    print("=== ESTADÍSTICAS DE VECTORES ===")
    
    # Total vectores
    cur.execute("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
    total = cur.fetchone()[0]
    print(f"Total vectores: {total:,}")
    
    # Por proyecto
    cur.execute("""
        SELECT project_id, COUNT(*) as count
        FROM document_chunks 
        WHERE embedding IS NOT NULL
        GROUP BY project_id
        ORDER BY count DESC
    """)
    
    print("\nDistribución por proyecto:")
    for proj, count in cur.fetchall():
        percentage = (count / total) * 100
        print(f"  {proj or 'Sin proyecto'}: {count:,} ({percentage:.1f}%)")
    
    # Documentos únicos
    cur.execute("SELECT COUNT(DISTINCT document_id) FROM document_chunks WHERE embedding IS NOT NULL")
    unique_docs = cur.fetchone()[0]
    print(f"\nDocumentos únicos vectorizados: {unique_docs:,}")
    print(f"Promedio chunks por documento: {total/unique_docs:.1f}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Uso:")
        print("  python view_vectors.py stats                    # Estadísticas")
        print("  python view_vectors.py all [limit] [offset]     # Ver todos (default: 50)")
        print("  python view_vectors.py project [project_id]     # Por proyecto")
        print("  python view_vectors.py search [término]         # Buscar contenido")
        print("  python view_vectors.py full [limit]             # Ver vectores completos")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "stats":
        vector_stats()
    
    elif command == "all":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        offset = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        view_all_vectors(limit, offset)
    
    elif command == "project":
        project_id = sys.argv[2] if len(sys.argv) > 2 else None
        view_vectors_by_project(project_id)
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("Error: Especifica un término de búsqueda")
            sys.exit(1)
        search_term = sys.argv[2]
        search_vectors_by_content(search_term)
    
    elif command == "full":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        view_all_vectors(limit, 0, show_full_vector=True)
    
    else:
        print(f"Comando desconocido: {command}")