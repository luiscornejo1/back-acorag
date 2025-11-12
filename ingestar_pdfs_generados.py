"""
Ingesta los PDFs generados en la base de datos
Extrae texto real de los PDFs y genera embeddings
"""
import os
import json
from pathlib import Path
from tqdm import tqdm
from app.upload import DocumentUploader

def main():
    print("📄 Ingesta de PDFs generados")
    print("=" * 60)
    
    # Rutas
    pdf_folder = "data/pdfs_generados"
    json_path = "data/mis_correos_con_contenido_sintetico.json"
    
    # Verificar que existan los PDFs
    if not os.path.exists(pdf_folder):
        print(f"❌ No se encontró la carpeta: {pdf_folder}")
        print("   Ejecuta primero: python generar_pdfs.py")
        return
    
    # Contar PDFs
    pdf_files = list(Path(pdf_folder).glob("*.pdf"))
    print(f"📁 Encontrados {len(pdf_files)} PDFs en {pdf_folder}")
    
    if len(pdf_files) == 0:
        print("❌ No hay PDFs para ingestar")
        return
    
    # Cargar JSON para obtener metadata adicional
    print(f"📖 Cargando metadata desde: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        documents_json = json.load(f)
    
    # Crear mapa de número de documento a metadata
    doc_map = {}
    for doc in documents_json:
        doc_number = doc.get('number', '')
        if doc_number:
            doc_map[doc_number] = doc
    
    print(f"✅ Metadata cargada para {len(doc_map)} documentos")
    
    # Preguntar si limpiar BD primero
    print("\n⚠️  ¿Deseas limpiar la base de datos antes de ingestar?")
    print("   Esto eliminará TODOS los documentos existentes (incluyendo el CV subido)")
    print("   1. Sí, limpiar primero (recomendado)")
    print("   2. No, agregar a los existentes")
    
    choice = input("\nSelecciona opción (1/2): ").strip()
    
    if choice == "1":
        print("\n🧹 Limpiando base de datos...")
        from limpiar_todo_force import limpiar_todo
        limpiar_todo()
        print("✅ Base de datos limpiada")
    
    # Inicializar uploader
    print("\n🚀 Iniciando ingesta...")
    uploader = DocumentUploader()
    
    # Contadores
    successful = 0
    failed = 0
    skipped = 0
    
    # Ingestar cada PDF
    for pdf_path in tqdm(pdf_files, desc="Ingiriendo PDFs"):
        try:
            filename = pdf_path.name
            
            # Extraer número de documento del nombre del archivo
            doc_number = filename.replace('.pdf', '')
            
            # Obtener metadata del JSON
            metadata = None
            if doc_number in doc_map:
                doc_data = doc_map[doc_number]
                metadata = {
                    "project_id": doc_data.get('project_id', 'UNKNOWN'),
                    "doc_type": doc_data.get('doc_type', 'documento'),
                    "title": doc_data.get('title', doc_number),
                    "category": doc_data.get('category', ''),
                    "status": doc_data.get('status', ''),
                }
            
            # Leer contenido del PDF
            with open(pdf_path, 'rb') as f:
                content = f.read()
            
            # Ingestar usando el uploader
            from app.upload import upload_and_ingest
            result = upload_and_ingest(content, filename, metadata)
            
            successful += 1
            
        except Exception as e:
            error_msg = str(e)
            
            # Si ya existe, contar como skipped
            if "ya existe" in error_msg.lower():
                skipped += 1
            else:
                failed += 1
                if failed <= 5:  # Solo mostrar primeros 5 errores
                    tqdm.write(f"❌ Error en {filename}: {error_msg[:100]}")
    
    # Resumen
    print("\n" + "=" * 60)
    print("✅ Ingesta completada")
    print(f"   📊 Exitosos: {successful}")
    print(f"   ⏭️  Omitidos (ya existían): {skipped}")
    print(f"   ❌ Fallidos: {failed}")
    print(f"   📈 Total procesados: {len(pdf_files)}")
    
    if successful > 0:
        print(f"\n🎯 Próximos pasos:")
        print(f"   1. Prueba búsquedas en el frontend")
        print(f"   2. Verifica que los scores sean > 0.5")
        print(f"   3. Usa el chat para hacer preguntas")

if __name__ == "__main__":
    main()
