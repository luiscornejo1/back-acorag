"""
Script para convertir contenido sintético en PDFs
Genera un PDF por cada documento en el JSON
"""
import json
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from tqdm import tqdm

def crear_pdf_documento(doc, output_dir="data/pdfs_generados"):
    """
    Crea un PDF para un documento usando su contenido sintético
    """
    try:
        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Nombre del PDF basado en número de documento o ID
        metadata = doc.get("metadata", {})
        doc_number = metadata.get("DocumentNumber", "")
        doc_id = doc.get("DocumentId", "")
        
        if doc_number:
            filename = f"{doc_number}.pdf"
        else:
            filename = f"DOC_{doc_id}.pdf"
        
        # Sanitizar nombre de archivo
        filename = filename.replace("/", "_").replace("\\", "_").replace(":", "_")
        filepath = os.path.join(output_dir, filename)
        
        # Crear PDF
        doc_pdf = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor='#1f4788',
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor='#2c5aa0',
            spaceAfter=6,
            spaceBefore=12
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        # Agregar título
        title = metadata.get("Title", "Documento sin título")
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Agregar información del documento
        info_lines = [
            f"<b>Número de Documento:</b> {metadata.get('DocumentNumber', 'N/A')}",
            f"<b>Tipo:</b> {metadata.get('DocumentType', 'N/A')}",
            f"<b>Categoría:</b> {metadata.get('Category', 'N/A')}",
            f"<b>Estado:</b> {metadata.get('DocumentStatus', 'N/A')}",
            f"<b>Revisión:</b> {metadata.get('Revision', 'N/A')}",
            f"<b>Proyecto:</b> {metadata.get('SelectList2', 'N/A')}",
            f"<b>Fecha de Modificación:</b> {metadata.get('DateModified', 'N/A')}",
        ]
        
        for line in info_lines:
            story.append(Paragraph(line, normal_style))
        
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("<b>─────────────────────────────────────────</b>", normal_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Agregar contenido sintético
        content = doc.get("synthetic_content", "")
        if content:
            # Dividir en párrafos
            paragraphs = content.split("\n\n")
            for para in paragraphs:
                para = para.strip()
                if para:
                    # Detectar si es título/encabezado
                    if para.isupper() or para.startswith("1.") or para.startswith("2."):
                        story.append(Paragraph(para, heading_style))
                    else:
                        # Reemplazar saltos de línea por <br/>
                        para = para.replace("\n", "<br/>")
                        story.append(Paragraph(para, normal_style))
                    story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph("<i>No hay contenido disponible</i>", normal_style))
        
        # Construir PDF
        doc_pdf.build(story)
        return filepath
    
    except Exception as e:
        print(f"\n❌ Error creando PDF para {doc.get('DocumentId')}: {e}")
        return None


def main():
    print("📄 GENERADOR DE PDFs DESDE CONTENIDO SINTÉTICO")
    print("=" * 60)
    
    # Verificar si reportlab está instalado
    try:
        import reportlab
    except ImportError:
        print("❌ Error: Necesitas instalar reportlab")
        print("   Ejecuta: pip install reportlab")
        return
    
    # Leer JSON con contenido sintético
    json_path = "data/mis_correos_con_contenido_sintetico.json"
    if not os.path.exists(json_path):
        print(f"❌ No se encuentra {json_path}")
        print("   Primero ejecuta: python generar_contenido_sintetico.py")
        return
    
    print(f"📖 Leyendo {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    print(f"✅ Cargados {len(documents)} documentos")
    
    # Preguntar cuántos PDFs generar
    print("\n💡 Opciones:")
    print("1. Generar TODOS los PDFs")
    print("2. Generar solo una MUESTRA (ej: 10, 50, 100)")
    
    opcion = input("\nSelecciona opción (1/2): ").strip()
    
    if opcion == "1":
        docs_to_process = documents
    elif opcion == "2":
        cantidad = int(input("¿Cuántos PDFs generar? "))
        docs_to_process = documents[:cantidad]
    else:
        print("❌ Opción inválida")
        return
    
    # Generar PDFs
    print(f"\n🚀 Generando {len(docs_to_process)} PDFs...")
    print("📁 Guardando en: data/pdfs_generados/\n")
    
    exitosos = 0
    for doc in tqdm(docs_to_process, desc="Generando PDFs"):
        filepath = crear_pdf_documento(doc)
        if filepath:
            exitosos += 1
    
    print(f"\n✅ ¡Completado!")
    print(f"\n📊 RESUMEN:")
    print(f"   - PDFs generados: {exitosos}")
    print(f"   - PDFs con error: {len(docs_to_process) - exitosos}")
    print(f"   - Directorio: data/pdfs_generados/")
    
    # Mostrar ejemplo
    if exitosos > 0:
        print(f"\n💡 Puedes abrir los PDFs con cualquier visor de PDF")
        print(f"   Ejemplo: data/pdfs_generados/{os.listdir('data/pdfs_generados')[0]}")


if __name__ == "__main__":
    main()
