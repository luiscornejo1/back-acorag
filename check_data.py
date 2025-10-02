#!/usr/bin/env python3
"""
Script para verificar datos existentes sin hacer nueva ingesta
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_existing_data():
    """Verificar qué datos ya existen en la base de datos"""
    
    print("🔍 VERIFICANDO DATOS EXISTENTES")
    print("=" * 50)
    
    try:
        # Conectar a BD
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        
        # Verificar documentos
        cur.execute("SELECT COUNT(*) FROM documents")
        doc_count = cur.fetchone()[0]
        
        # Verificar chunks
        cur.execute("SELECT COUNT(*) FROM document_chunks")
        chunk_count = cur.fetchone()[0]
        
        # Verificar proyectos
        cur.execute("""
            SELECT project_id, COUNT(*) as doc_count 
            FROM documents 
            GROUP BY project_id 
            ORDER BY doc_count DESC 
            LIMIT 5
        """)
        projects = cur.fetchall()
        
        # Verificar tipos de documentos
        cur.execute("""
            SELECT doc_type, COUNT(*) as count 
            FROM documents 
            WHERE doc_type IS NOT NULL 
            GROUP BY doc_type 
            ORDER BY count DESC 
            LIMIT 5
        """)
        doc_types = cur.fetchall()
        
        # Resultados
        print(f"📊 RESUMEN DE DATOS:")
        print(f"   • Documentos totales: {doc_count:,}")
        print(f"   • Chunks vectoriales: {chunk_count:,}")
        
        if doc_count > 0:
            print(f"\n✅ DATOS YA CARGADOS - No necesitas hacer ingesta")
            
            print(f"\n🏗️ Top proyectos:")
            for proj_id, count in projects:
                print(f"   • {proj_id}: {count:,} documentos")
            
            print(f"\n📄 Tipos de documentos:")
            for doc_type, count in doc_types:
                print(f"   • {doc_type}: {count:,}")
                
            # Verificar índices vectoriales
            cur.execute("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE tablename = 'document_chunks' 
                AND indexname LIKE '%embedding%'
            """)
            indexes = cur.fetchall()
            
            if indexes:
                print(f"\n🚀 Índices vectoriales activos:")
                for idx_name, table in indexes:
                    print(f"   • {idx_name}")
            
        else:
            print(f"\n❌ NO HAY DATOS - Necesitas hacer ingesta")
            print(f"Ejecuta: python -m app.ingest --json_path data/mis_correos.json --project_id EDUCACION_PROJECT")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
        print(f"💡 Asegúrate de que PostgreSQL esté corriendo")

if __name__ == "__main__":
    check_existing_data()