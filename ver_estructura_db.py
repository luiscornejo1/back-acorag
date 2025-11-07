"""
Script para ver la estructura de las tablas en Railway
"""
import psycopg2
import os

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

print("="*60)
print("ESTRUCTURA DE TABLAS EN RAILWAY")
print("="*60)

# Ver si existen las tablas
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
""")

print("\n📋 Tablas existentes:")
tables = cur.fetchall()
for t in tables:
    print(f"  - {t[0]}")

# Ver columnas de document_chunks si existe
cur.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'document_chunks'
    ORDER BY ordinal_position
""")

print("\n📊 Columnas de 'document_chunks':")
columns = cur.fetchall()
if columns:
    for col in columns:
        print(f"  - {col[0]}: {col[1]}")
else:
    print("  ⚠️  La tabla 'document_chunks' NO EXISTE")

# Ver columnas de documents si existe
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'documents'
    ORDER BY ordinal_position
""")

print("\n📊 Columnas de 'documents':")
columns = cur.fetchall()
if columns:
    for col in columns:
        print(f"  - {col[0]}: {col[1]}")
else:
    print("  ⚠️  La tabla 'documents' NO EXISTE")

# Ver extensiones instaladas
cur.execute("SELECT extname FROM pg_extension")
print("\n🔌 Extensiones instaladas:")
for ext in cur.fetchall():
    print(f"  - {ext[0]}")

cur.close()
conn.close()

print("\n" + "="*60)
