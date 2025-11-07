"""
Ver project_ids existentes en la base de datos
"""
import psycopg2
import os

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

# Ver si existe la tabla documents
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'documents'
    )
""")

if cur.fetchone()[0]:
    # Ver project_ids únicos
    cur.execute("""
        SELECT DISTINCT project_id, COUNT(*) as doc_count
        FROM documents
        GROUP BY project_id
        ORDER BY doc_count DESC
    """)
    
    results = cur.fetchall()
    
    print("📊 Project IDs existentes:")
    print("="*50)
    if results:
        for proj_id, count in results:
            print(f"  • {proj_id}: {count} documentos")
    else:
        print("  ⚠️  No hay documentos en la base de datos")
else:
    print("⚠️  La tabla 'documents' no existe aún")
    print("💡 Puedes usar cualquier project_id, por ejemplo: 'ACONEX'")

cur.close()
conn.close()
