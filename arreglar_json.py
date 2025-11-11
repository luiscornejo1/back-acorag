"""
Script para arreglar el formato del JSON
(convierte múltiples objetos JSON en un array válido)
"""
import json

print("🔧 Arreglando formato de mis_correos_optimizado.json...")

# Leer línea por línea
documents = []
with open("data/mis_correos_optimizado.json", 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                doc = json.loads(line)
                documents.append(doc)
            except json.JSONDecodeError:
                continue

print(f"✅ Cargados {len(documents)} documentos")

# Guardar como array JSON válido
print("💾 Guardando formato corregido...")
with open("data/mis_correos_optimizado.json", 'w', encoding='utf-8') as f:
    json.dump(documents, f, ensure_ascii=False, indent=2)

print(f"✅ Archivo corregido: {len(documents)} documentos en formato array JSON válido")
print("\n💡 Ahora ejecuta: python generar_contenido_sintetico.py")
