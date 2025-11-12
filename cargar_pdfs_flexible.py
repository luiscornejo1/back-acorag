"""
Script mejorado para cargar PDFs con matching flexible.
Hace match por número de documento en lugar de filename exacto.

Uso:
    python cargar_pdfs_flexible.py

Estrategia:
    1. Extrae el número del PDF (ej: 200076-CCC02-CR-CP-000013)
    2. Busca en BD por número (ignorando extensión y espacios)
    3. Actualiza file_content con el PDF
"""

import os
import re
import psycopg2
from psycopg2 import Binary
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("❌ ERROR: DATABASE_URL no configurada")

PDF_DIR = Path("data/pdfs_generados")
if not PDF_DIR.exists():
    raise SystemExit(f"❌ ERROR: No existe la carpeta {PDF_DIR}")

print(f"📂 Buscando PDFs en: {PDF_DIR}")
pdfs = list(PDF_DIR.glob("*.pdf"))
print(f"📄 Encontrados {len(pdfs)} archivos PDF")

if not pdfs:
    raise SystemExit("❌ No hay PDFs para cargar")

# Conectar a PostgreSQL
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

updated = 0
not_found = 0
errors = 0
skipped = 0

for pdf_path in pdfs:
    filename = pdf_path.name
    
    try:
        # Extraer el número base del archivo (sin extensión)
        # Ej: "200076-CCC02-CR-CP-000013.pdf" -> "200076-CCC02-CR-CP-000013"
        base_name = pdf_path.stem
        
        # Leer contenido binario del PDF
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        # Estrategia 1: Buscar por filename exacto
        cur.execute("""
            SELECT document_id, title, file_content IS NOT NULL as has_content
            FROM documents 
            WHERE filename = %s 
            LIMIT 1
        """, (filename,))
        
        row = cur.fetchone()
        
        # Estrategia 2: Si no se encontró, buscar por patrón flexible
        if not row:
            # Buscar filename que empiece con el base_name (ignora extensión y espacios)
            cur.execute("""
                SELECT document_id, title, filename, file_content IS NOT NULL as has_content
                FROM documents 
                WHERE filename LIKE %s
                   OR filename LIKE %s
                   OR filename = %s
                LIMIT 1
            """, (f"{base_name}.%", f"{base_name} .%", f"{base_name}"))
            
            row = cur.fetchone()
        
        if row:
            doc_id = row[0]
            title = row[1]
            has_content = row[2] if len(row) > 2 else row[2]
            
            # Solo actualizar si NO tiene contenido ya
            if has_content:
                skipped += 1
                if skipped <= 5:
                    print(f"⏭️  [{skipped}] Ya tiene PDF: {title[:50]}...")
                continue
            
            # Actualizar columna file_content con contenido binario
            cur.execute("""
                UPDATE documents 
                SET file_content = %s,
                    filename = %s
                WHERE document_id = %s
            """, (Binary(pdf_bytes), filename, doc_id))
            
            updated += 1
            if updated % 100 == 0:
                print(f"✅ [{updated}] Actualizados hasta ahora...")
            elif updated <= 10:
                print(f"✅ [{updated}] Actualizado: {title[:50]}... ({len(pdf_bytes):,} bytes)")
        else:
            not_found += 1
            if not_found <= 10:  # Solo mostrar primeros 10
                print(f"⚠️  No encontrado en BD: {filename} (base: {base_name})")
    
    except Exception as e:
        errors += 1
        print(f"❌ Error con {filename}: {e}")

# Confirmar cambios
conn.commit()

# Mostrar estadísticas finales
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(file_content) as with_pdf,
        COUNT(*) - COUNT(file_content) as without_pdf
    FROM documents
""")
stats = cur.fetchone()

cur.close()
conn.close()

print("\n" + "="*70)
print(f"📊 RESUMEN:")
print(f"   ✅ Actualizados: {updated}")
print(f"   ⏭️  Ya tenían PDF (omitidos): {skipped}")
print(f"   ⚠️  No encontrados en BD: {not_found}")
print(f"   ❌ Errores: {errors}")
print("="*70)

print("\n📈 ESTADÍSTICAS FINALES DE LA BD:")
print(f"   Total documentos: {stats[0]}")
print(f"   Con PDF: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
print(f"   Sin PDF: {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
print("="*70)

if updated > 0:
    print(f"\n🎉 ¡Éxito! {updated} documentos ahora tienen PDF en file_content")
    print("   → Despliega los cambios del backend a Railway:")
    print("      git add .")
    print('      git commit -m "feat: Add file_content column for PDF storage"')
    print("      git push")
    print("\n   → Luego podrás ver los PDFs en el frontend haciendo clic en 'Ver PDF'")
