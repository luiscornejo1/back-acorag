#!/usr/bin/env python3
"""
Script para cargar emails al sistema de documentos Aconex
Convierte emails a formato de documentos para búsqueda semántica
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from app.ingest import main, iter_docs_from_file

def convert_email_to_aconex_doc(email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte un email al formato esperado por ingest.py (documentos Aconex)
    """
    # Crear DocumentId único
    document_id = email.get('id', f"email_{hash(str(email))}")
    
    # Construir metadata en formato Aconex
    metadata = {
        "Title": email.get('subject', 'Email sin asunto'),
        "DocumentNumber": document_id,
        "Category": "Email",
        "DocumentType": "Correo Electrónico", 
        "DocumentStatus": "Active",
        "ReviewStatus": "Approved",
        "Revision": "1",
        "Filename": f"{document_id}.eml",
        "FileType": "email",
        "FileSize": len(str(email)),
        "DateModified": email.get('sent_date', datetime.now().isoformat()),
        
        # Campos específicos del email
        "SelectList1": email.get('sender', ''),  # Remitente
        "SelectList2": email.get('project_id', 'EMAIL_PROJECT'),  # Proyecto
        "SelectList3": email.get('recipient', ''),  # Destinatario
        
        # Contenido del email
        "Description": email.get('body', ''),
        "Notes": f"De: {email.get('sender', '')}\nPara: {email.get('recipient', '')}"
    }
    
    # Crear documento en formato Aconex
    aconex_doc = {
        "DocumentId": document_id,
        "project_id": email.get('project_id', 'EMAIL_PROJECT'),
        "metadata": metadata
    }
    
    return aconex_doc

def convert_emails_file():
    """
    Convierte el archivo de emails al formato Aconex y lo guarda
    """
    print("🔄 Convirtiendo emails a formato Aconex...")
    
    input_file = "data/mis_correos.json"
    output_file = "data/emails_aconex_format.json"
    
    # Verificar que el archivo de entrada existe
    if not os.path.exists(input_file):
        print(f"❌ No se encuentra el archivo: {input_file}")
        return None
    
    try:
        # Leer emails originales
        with open(input_file, 'r', encoding='utf-8') as f:
            emails = json.load(f)
        
        print(f"📧 Encontrados {len(emails)} emails")
        
        # Convertir a formato Aconex
        aconex_docs = []
        for i, email in enumerate(emails):
            try:
                aconex_doc = convert_email_to_aconex_doc(email)
                aconex_docs.append(aconex_doc)
                if (i + 1) % 100 == 0:
                    print(f"   Procesados {i + 1} emails...")
            except Exception as e:
                print(f"⚠️ Error procesando email {email.get('id', 'sin_id')}: {e}")
        
        # Guardar en formato Aconex
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(aconex_docs, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Convertidos {len(aconex_docs)} documentos")
        print(f"📁 Guardado en: {output_file}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error leyendo archivo de emails: {e}")
        return None

def load_emails_to_database():
    """
    Carga los emails convertidos a la base de datos usando ingest.py
    """
    print("🚀 Iniciando carga a base de datos...")
    
    # Convertir emails
    aconex_file = convert_emails_file()
    
    if not aconex_file:
        print("❌ No se pudo convertir el archivo de emails")
        return
    
    # Usar el sistema de ingesta existente
    try:
        main(
            json_path=aconex_file,
            project_id="EMAIL_PROJECT",  # Proyecto por defecto
            batch_size=50  # Lotes más pequeños para emails
        )
        print("🎉 ¡Emails cargados exitosamente!")
        
        # Mostrar estadísticas
        from app.ingest import connect_db
        conn = connect_db()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM documents WHERE doc_type = 'Correo Electrónico'")
            doc_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM document_chunks WHERE project_id = 'EMAIL_PROJECT'")
            chunk_count = cur.fetchone()[0]
            
            print(f"📊 Estadísticas:")
            print(f"   - Documentos (emails): {doc_count}")
            print(f"   - Chunks para búsqueda: {chunk_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error en la carga: {e}")
        print("💡 Verifica que:")
        print("   - PostgreSQL esté corriendo")
        print("   - DATABASE_URL esté configurada en .env")
        print("   - Las tablas estén creadas")
        raise

if __name__ == "__main__":
    load_emails_to_database()