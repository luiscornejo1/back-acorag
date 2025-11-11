"""
Script para ver ejemplos del contenido sintético generado
"""
import json
import os

json_path = "data/mis_correos_con_contenido_sintetico.json"

if not os.path.exists(json_path):
    print(f"❌ No se encuentra {json_path}")
    print("Primero ejecuta: python generar_contenido_sintetico.py")
    exit(1)

print("📖 Leyendo ejemplos del contenido generado...")
with open(json_path, 'r', encoding='utf-8') as f:
    documents = json.load(f)

print(f"✅ Total documentos: {len(documents)}")
print("\n" + "="*80)

# Mostrar 3 ejemplos
for i, doc in enumerate(documents[:3], 1):
    print(f"\n📄 EJEMPLO {i}")
    print("="*80)
    print(f"DocumentId: {doc['DocumentId']}")
    print(f"Título: {doc['metadata'].get('Title', 'N/A')}")
    print(f"Tipo: {doc['metadata'].get('DocumentType', 'N/A')}")
    print(f"Número: {doc['metadata'].get('DocumentNumber', 'N/A')}")
    print(f"\n--- METADATA OPTIMIZADO (primeros 200 chars) ---")
    print(doc.get('enriched_metadata_text', '')[:200] + "...")
    print(f"\n--- CONTENIDO SINTÉTICO GENERADO (primeros 500 chars) ---")
    print(doc.get('synthetic_content', '')[:500] + "...")
    print(f"\n📏 Longitud total del full_text: {len(doc.get('full_text', ''))} caracteres")
    print("="*80)

print(f"\n💡 Si el contenido se ve bien, procede a ingestar con:")
print(f"   python -m app.ingest --json_path {json_path} --project_id ACONEX")
