"""
Script para investigar por qué 335 PDFs no se encontraron en la BD.
"""

import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
PDF_DIR = Path("data/pdfs_generados")

# Conectar a BD
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Obtener TODOS los filenames de la BD
cur.execute("SELECT DISTINCT filename FROM documents WHERE filename IS NOT NULL AND filename != ''")
db_filenames = {row[0] for row in cur.fetchall()}
print(f"📊 Filenames en BD: {len(db_filenames)}")

# Obtener TODOS los PDFs del disco
pdf_files = {p.name for p in PDF_DIR.glob("*.pdf")}
print(f"📂 PDFs en disco: {len(pdf_files)}")

# Encontrar diferencias
pdfs_not_in_db = pdf_files - db_filenames
db_not_in_pdfs = db_filenames - pdf_files

print(f"\n" + "="*70)
print(f"🔍 ANÁLISIS DE DIFERENCIAS:")
print("="*70)

print(f"\n1️⃣  PDFs en disco pero NO en BD: {len(pdfs_not_in_db)}")
if pdfs_not_in_db:
    print("   Primeros 10 ejemplos:")
    for i, fname in enumerate(sorted(pdfs_not_in_db)[:10], 1):
        print(f"   {i}. {fname}")

print(f"\n2️⃣  Filenames en BD pero NO hay PDF en disco: {len(db_not_in_pdfs)}")
if db_not_in_pdfs:
    print("   Primeros 10 ejemplos:")
    for i, fname in enumerate(sorted(db_not_in_pdfs)[:10], 1):
        print(f"   {i}. {fname}")

# Revisar si hay diferencias en formato (espacios, mayúsculas, etc)
print(f"\n3️⃣  Verificando posibles problemas de formato...")

# Verificar PDFs con nombres similares pero diferentes
similar_issues = []
for pdf_name in list(pdfs_not_in_db)[:20]:  # Solo primeros 20 para no saturar
    # Buscar nombres similares en BD (case-insensitive)
    pdf_lower = pdf_name.lower()
    for db_name in db_filenames:
        if db_name.lower() == pdf_lower and db_name != pdf_name:
            similar_issues.append({
                'pdf': pdf_name,
                'db': db_name,
                'issue': 'Diferencia de mayúsculas/minúsculas'
            })

if similar_issues:
    print(f"   ⚠️  Encontrados {len(similar_issues)} casos con diferencias de formato:")
    for issue in similar_issues[:5]:
        print(f"      • PDF: {issue['pdf']}")
        print(f"        BD:  {issue['db']}")
        print(f"        Problema: {issue['issue']}\n")

# Estadísticas de proyectos
print(f"\n4️⃣  Distribución por proyecto:")
cur.execute("""
    SELECT project_id, COUNT(*), COUNT(file_content) as with_pdf
    FROM documents
    GROUP BY project_id
    ORDER BY COUNT(*) DESC
""")
for project, total, with_pdf in cur.fetchall():
    percentage = (with_pdf / total * 100) if total > 0 else 0
    print(f"   {project}: {with_pdf}/{total} con PDF ({percentage:.1f}%)")

cur.close()
conn.close()

print("\n" + "="*70)
print("✅ Análisis completado")
print("="*70)
