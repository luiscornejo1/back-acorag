"""
Script para OPTIMIZAR metadatos cuando NO tienes acceso a PDFs
Estrategia: Expandir y enriquecer los metadatos existentes para maximizar búsqueda semántica
"""

import json
import os
from typing import Dict, List, Any
from pathlib import Path

# =============================================
# CONFIGURACIÓN
# =============================================

INPUT_JSON = "data/mis_correos.json"
OUTPUT_JSON = "data/mis_correos_optimizado.json"

# Mapeo de campos técnicos a lenguaje natural en ESPAÑOL
FIELD_TRANSLATIONS = {
    "DocumentId": "Identificador del documento",
    "DocumentNumber": "Número de documento",
    "Title": "Título",
    "Category": "Categoría",
    "DocumentType": "Tipo de documento",
    "DocumentStatus": "Estado del documento",
    "ReviewStatus": "Estado de revisión",
    "Revision": "Revisión",
    "Filename": "Nombre del archivo",
    "FileType": "Tipo de archivo",
    "FileSize": "Tamaño del archivo",
    "DateModified": "Fecha de modificación",
    "MilestoneDate": "Fecha de hito",
    "SelectList1": "Ubicación/Área",
    "SelectList2": "Proyecto",
    "SelectList3": "Disciplina",
    "SelectList4": "Clasificación",
    "SelectList5": "Fase",
    "SelectList6": "Responsable",
    "SelectList7": "Contratista",
    "SelectList8": "Especialidad",
    "SelectList9": "Estado adicional",
    "SelectList10": "Información complementaria",
}

# =============================================
# FUNCIONES
# =============================================

def load_documents(json_path: str) -> List[Dict]:
    """Carga documentos desde JSON/NDJSON"""
    docs = []
    
    # Intentar JSON completo
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return [data]
    except:
        pass
    
    # NDJSON
    with open(json_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))
    
    return docs

def optimize_metadata(doc: Dict) -> Dict:
    """
    Expande metadatos creando un campo de texto enriquecido
    para mejorar la búsqueda semántica
    """
    metadata = doc.get('metadata', {})
    
    # Crear descripción expandida en lenguaje natural
    enriched_lines = []
    
    # 1. INFORMACIÓN PRINCIPAL (repetida para mayor peso)
    title = metadata.get('Title', '')
    doc_number = metadata.get('DocumentNumber', '')
    doc_type = metadata.get('DocumentType', '')
    
    if title:
        enriched_lines.extend([
            f"Este es un documento titulado: {title}",
            f"El documento se llama: {title}",
            f"Título del documento: {title}",
        ])
    
    if doc_number:
        enriched_lines.extend([
            f"Número de documento: {doc_number}",
            f"Identificado con el número: {doc_number}",
        ])
    
    if doc_type:
        enriched_lines.extend([
            f"Es un documento de tipo: {doc_type}",
            f"Clasificado como: {doc_type}",
        ])
    
    # 2. CONTEXTO DEL PROYECTO
    project = metadata.get('SelectList2', '')
    location = metadata.get('SelectList1', '')
    discipline = metadata.get('SelectList3', '')
    
    if project:
        enriched_lines.extend([
            f"Pertenece al proyecto: {project}",
            f"Proyecto asociado: {project}",
        ])
    
    if location:
        enriched_lines.append(f"Ubicación o área: {location}")
    
    if discipline:
        enriched_lines.append(f"Disciplina técnica: {discipline}")
    
    # 3. ESTADOS Y REVISIÓN
    status = metadata.get('DocumentStatus', '')
    review_status = metadata.get('ReviewStatus', '')
    revision = metadata.get('Revision', '')
    
    if status:
        enriched_lines.append(f"Estado actual del documento: {status}")
    
    if review_status:
        enriched_lines.append(f"Estado de revisión: {review_status}")
    
    if revision:
        enriched_lines.append(f"Revisión número: {revision}")
    
    # 4. TODOS LOS CAMPOS TRADUCIDOS
    for field, translation in FIELD_TRANSLATIONS.items():
        value = metadata.get(field)
        if value and str(value).strip():
            enriched_lines.append(f"{translation}: {value}")
    
    # 5. CAMPOS ADICIONALES (SelectList4-10)
    for i in range(4, 11):
        field = f"SelectList{i}"
        value = metadata.get(field)
        if value and str(value).strip():
            enriched_lines.append(f"Información adicional {i-3}: {value}")
    
    # 6. INFORMACIÓN DE ARCHIVO
    filename = metadata.get('Filename', '')
    file_type = metadata.get('FileType', '')
    
    if filename:
        enriched_lines.append(f"Nombre del archivo: {filename}")
        # Extraer información del nombre del archivo
        if '_' in filename or '-' in filename:
            enriched_lines.append(f"Detalles del nombre: {filename.replace('_', ' ').replace('-', ' ')}")
    
    if file_type:
        enriched_lines.append(f"Formato del archivo: {file_type}")
    
    # 7. RESUMEN FINAL (para búsquedas generales)
    summary_parts = []
    if doc_type:
        summary_parts.append(f"documento tipo {doc_type}")
    if doc_number:
        summary_parts.append(f"número {doc_number}")
    if project:
        summary_parts.append(f"del proyecto {project}")
    
    if summary_parts:
        enriched_lines.append(f"Resumen: {' '.join(summary_parts)}")
    
    # Crear campo de texto enriquecido
    enriched_text = "\n".join(enriched_lines)
    
    # Agregar el campo al documento
    doc['enriched_metadata_text'] = enriched_text
    
    return doc

# =============================================
# MAIN
# =============================================

def main():
    print("🚀 Optimizando metadatos para búsqueda sin PDFs...\n")
    
    # Cargar documentos
    print(f"📖 Cargando documentos desde {INPUT_JSON}...")
    docs = load_documents(INPUT_JSON)
    print(f"✅ {len(docs)} documentos cargados\n")
    
    # Optimizar metadatos
    print("🔄 Enriqueciendo metadatos...")
    optimized_docs = []
    
    for i, doc in enumerate(docs, 1):
        optimized_doc = optimize_metadata(doc)
        optimized_docs.append(optimized_doc)
        
        if i % 1000 == 0:
            print(f"   Procesados: {i}/{len(docs)}")
    
    # Guardar documentos optimizados
    print(f"\n💾 Guardando documentos optimizados en {OUTPUT_JSON}...")
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        for doc in optimized_docs:
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')
    
    # Estadísticas
    avg_length = sum(len(d.get('enriched_metadata_text', '')) for d in optimized_docs) / len(optimized_docs)
    
    print("\n" + "="*50)
    print("📊 RESUMEN")
    print("="*50)
    print(f"✅ Documentos optimizados: {len(optimized_docs)}")
    print(f"📝 Longitud promedio de texto enriquecido: {int(avg_length)} caracteres")
    print(f"📁 Archivo guardado: {OUTPUT_JSON}")
    
    # Mostrar ejemplo
    print("\n" + "="*50)
    print("📄 EJEMPLO DE DOCUMENTO OPTIMIZADO")
    print("="*50)
    if optimized_docs:
        example = optimized_docs[0]
        print(f"\nOriginal Title: {example.get('metadata', {}).get('Title', 'N/A')}")
        print(f"\nTexto enriquecido ({len(example.get('enriched_metadata_text', ''))} chars):")
        print("-" * 50)
        print(example.get('enriched_metadata_text', '')[:500] + "...")
    
    print("\n💡 Próximos pasos:")
    print("1. Actualiza EMBEDDING_MODEL en Railway a: dccuchile/bert-base-spanish-wwm-uncased")
    print("2. Re-ingesta con:")
    print(f"   python -m app.ingest --json_path {OUTPUT_JSON} --project_id TU_PROYECTO")

if __name__ == "__main__":
    main()
