"""
Script para cargar los PDFs desde data/pdfs_generados/ a la columna 'raw' de la BD.

Uso:
    python cargar_pdfs_a_bd.py

Requisitos:
    - DATABASE_URL en variables de entorno o .env
    - Carpeta data/pdfs_generados/ con los PDFs generados
"""

import os
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

for pdf_path in pdfs:
    filename = pdf_path.name
    
    try:
        # Leer contenido binario del PDF
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        # Buscar documento por filename
        cur.execute("""
            SELECT document_id, title 
            FROM documents 
            WHERE filename = %s 
            LIMIT 1
        """, (filename,))
        
        row = cur.fetchone()
        
        if row:
            doc_id, title = row
            # Actualizar columna file_content con contenido binario (mantiene raw intacto)
            cur.execute("""
                UPDATE documents 
                SET file_content = %s 
                WHERE document_id = %s
            """, (Binary(pdf_bytes), doc_id))
            
            updated += 1
            print(f"✅ [{updated}] Actualizado: {title[:50]}... ({len(pdf_bytes):,} bytes)")
        else:
            not_found += 1
            if not_found <= 5:  # Solo mostrar primeros 5
                print(f"⚠️  No encontrado en BD: {filename}")
    
    except Exception as e:
        errors += 1
        print(f"❌ Error con {filename}: {e}")

# Confirmar cambios
conn.commit()
cur.close()
conn.close()

print("\n" + "="*70)
print(f"📊 RESUMEN:")
print(f"   ✅ Actualizados: {updated}")
print(f"   ⚠️  No encontrados en BD: {not_found}")
print(f"   ❌ Errores: {errors}")
print("="*70)

if updated > 0:
    print(f"\n🎉 ¡Éxito! {updated} documentos ahora tienen PDF en la columna 'raw'")
    print("   → Ahora puedes ver los PDFs en el frontend haciendo clic en 'Ver PDF'")
