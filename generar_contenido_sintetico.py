"""
Script para generar contenido sintético realista para cada documento
usando Groq LLM basándose en el metadata JSON.

Esto simula el contenido de PDFs que no están disponibles.
"""
import json
import os
from groq import Groq
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

import re
import time


class RateLimitError(Exception):
    """Raised when the LLM API returns a rate-limit / TPD error."""
    pass

def generar_contenido_documento(metadata: dict, client: Groq) -> str:
    """Genera contenido sintético realista para un documento basándose en su metadata usando Groq LLM.

    Esta versión detecta errores de rate-limit y lanza RateLimitError para que el llamador
    pueda aplicar backoff y reintentar.
    """
    doc_type = metadata.get("DocumentType", "Documento")
    title = metadata.get("Title", "Sin título")
    number = metadata.get("DocumentNumber", "")
    category = metadata.get("Category", "")
    status = metadata.get("DocumentStatus", "")
    project = metadata.get("SelectList2", "")
    discipline = metadata.get("SelectList7", "")
    revision = metadata.get("Revision", "")

    prompt = f"""Genera el contenido realista de un documento de construcción en español con las siguientes características:

INFORMACIÓN DEL DOCUMENTO:
- Tipo: {doc_type}
- Título: {title}
- Número: {number}
- Categoría: {category}
- Estado: {status}
- Proyecto: {project}
- Disciplina: {discipline}
- Revisión: {revision}

INSTRUCCIONES ESPECÍFICAS POR TIPO:

Si es "Plano":
- Describe especificaciones técnicas detalladas
- Menciona dimensiones, materiales, normas aplicables
- Include referencias a elementos estructurales/arquitectónicos
- Agrega notas técnicas y consideraciones de diseño

Si es "Informe":
- Estructura: Resumen ejecutivo, antecedentes, análisis, conclusiones
- Include datos numéricos realistas (porcentajes, fechas, cantidades)
- Menciona hallazgos, recomendaciones, acciones correctivas

Si es "Cronograma":
- Lista actividades con fechas específicas (usa formato DD/MM/AAAA)
- Menciona hitos importantes del proyecto
- Include recursos asignados, responsables
- Identifica posibles retrasos o riesgos

Si es "Especificación Técnica":
- Describe materiales, equipos, procedimientos
- Menciona normas técnicas (ASTM, ISO, etc.)
- Include requisitos de calidad, tolerancias
- Agrega procedimientos de instalación/ejecución

Si es "Procedimiento":
- Lista pasos numerados detalladamente
- Menciona equipos de seguridad requeridos
- Include precauciones y advertencias
- Agrega responsables y verificaciones

FORMATO:
- Genera entre 800-1200 palabras
- Usa formato profesional y técnico
- Include párrafos bien estructurados
- Menciona fechas específicas cuando sea relevante (relacionadas con {revision})
- Usa terminología técnica apropiada
- NO uses markdown, solo texto plano con saltos de línea

Genera SOLO el contenido del documento, SIN introducción ni explicaciones adicionales."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Eres un experto en documentos técnicos de construcción y arquitectura. Generas contenido realista y profesional para documentos técnicos basándose en metadata."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        msg = str(e)
        print(f"❌ Error generando contenido: {msg}")
        # Detectar límites (rate limit / TPD) por heurística en el mensaje
        if "rate limit" in msg.lower() or "rate_limit" in msg.lower() or "rate limit reached" in msg.lower() or "429" in msg:
            raise RateLimitError(msg)

        # Si no es rate-limit, devolvemos un fallback conservador
        return f"""DOCUMENTO: {title}
Número: {number}
Tipo: {doc_type}
Proyecto: {project}
Disciplina: {discipline}
Estado: {status}
Revisión: {revision}

Este documento forma parte del proyecto de construcción {project}.
Corresponde a la disciplina {discipline} y se encuentra en estado {status}.
La revisión actual es {revision}.

[Contenido generado automáticamente basado en metadata]"""


def main():
    print("🤖 GENERADOR DE CONTENIDO SINTÉTICO PARA DOCUMENTOS")
    print("=" * 60)
    
    # Verificar API key
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("❌ Error: GROQ_API_KEY no configurada en .env")
        return
    
    client = Groq(api_key=api_key)
    
    # Leer JSON optimizado
    json_path = "data/mis_correos_optimizado.json"
    if not os.path.exists(json_path):
        print(f"❌ Error: No se encuentra {json_path}")
        return
    
    print(f"📖 Leyendo {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    print(f"✅ Cargados {len(documents)} documentos")
    
    # Preguntar cuántos documentos generar
    print("\n💡 Opciones:")
    print("1. Generar TODOS los documentos (147K - tomará MUCHAS horas y dinero)")
    print("2. Generar una MUESTRA (ej: 100, 500, 1000 documentos)")
    print("3. Generar solo de CATEGORÍAS específicas")
    
    opcion = input("\nSelecciona opción (1/2/3): ").strip()
    
    if opcion == "1":
        docs_to_process = documents
        print(f"⚠️ ADVERTENCIA: Esto generará {len(documents)} documentos y costará ~$20-50 USD en API de Groq")
        confirm = input("¿Estás seguro? (si/no): ").strip().lower()
        if confirm != "si":
            print("❌ Cancelado")
            return
    
    elif opcion == "2":
        cantidad = int(input("¿Cuántos documentos generar? (ej: 100): ").strip())
        docs_to_process = documents[:cantidad]
        print(f"✅ Generando muestra de {len(docs_to_process)} documentos")
    
    elif opcion == "3":
        # Mostrar categorías disponibles
        categorias = set(doc.get("metadata", {}).get("Category", "Sin categoría") for doc in documents)
        print("\n📋 Categorías disponibles:")
        for i, cat in enumerate(sorted(categorias), 1):
            count = sum(1 for d in documents if d.get("metadata", {}).get("Category") == cat)
            print(f"   {i}. {cat} ({count} docs)")
        
        cat_seleccionada = input("\nEscribe el nombre de la categoría: ").strip()
        docs_to_process = [d for d in documents if d.get("metadata", {}).get("Category") == cat_seleccionada]
        print(f"✅ Generando {len(docs_to_process)} documentos de categoría '{cat_seleccionada}'")
    
    else:
        print("❌ Opción inválida")
        return
    
    # Generar contenido para cada documento
    print(f"\n🚀 Generando contenido sintético para {len(docs_to_process)} documentos...")
    print(f"💰 Costo estimado: ~${len(docs_to_process) * 0.0001:.2f} USD (usando llama-3.1-8b-instant)")
    print("⏱️ Estimado: ~2-3 segundos por documento\n")
    
    documentos_enriquecidos = []
    errores = 0

    # Soporte de checkpoint/resume: si ya existe output, lo cargamos y continuamos
    output_path = "data/mis_correos_con_contenido_sintetico.json"
    checkpoint_path = "data/generate_checkpoint.json"

    start_index = 0
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                documentos_enriquecidos = json.load(f)
            start_index = len(documentos_enriquecidos)
            print(f"🔁 Reanudando desde índice {start_index} (archivo existente: {output_path})")
        except Exception:
            documentos_enriquecidos = []
            start_index = 0

    total = len(docs_to_process)
    for idx in range(start_index, total):
        doc = docs_to_process[idx]
        metadata = doc.get("metadata", {})

        max_retries = 6
        retry_count = 0
        backoff = 5

        while True:
            try:
                contenido_generado = generar_contenido_documento(metadata, client)

                doc_enriquecido = {
                    "DocumentId": doc["DocumentId"],
                    "metadata": metadata,
                    "enriched_metadata_text": doc.get("enriched_metadata_text", ""),
                    "synthetic_content": contenido_generado,
                    "full_text": f"{doc.get('enriched_metadata_text', '')}\n\n===== CONTENIDO DEL DOCUMENTO =====\n\n{contenido_generado}"
                }

                documentos_enriquecidos.append(doc_enriquecido)

                # Guardar progreso periódico
                if (idx + 1) % 10 == 0 or (idx + 1) == total:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(documentos_enriquecidos, f, ensure_ascii=False, indent=2)
                    with open(checkpoint_path, 'w', encoding='utf-8') as cf:
                        json.dump({"last_index": idx + 1}, cf)

                break

            except RateLimitError as rl:
                msg = str(rl)
                wait_seconds = None
                m = re.search(r"(\d+)m(\d+(?:\.\d+)?)s", msg)
                if m:
                    minutes = int(m.group(1))
                    seconds = float(m.group(2))
                    wait_seconds = minutes * 60 + seconds
                else:
                    m2 = re.search(r"(\d+(?:\.\d+)?)s", msg)
                    if m2:
                        wait_seconds = float(m2.group(1))

                if wait_seconds is None:
                    wait_seconds = backoff

                wait_seconds = max(wait_seconds, backoff) + 2
                retry_count += 1
                if retry_count > max_retries:
                    print(f"❌ Máximo reintentos alcanzado para documento {doc.get('DocumentId')}. Saltando.")
                    errores += 1
                    doc_enriquecido = {
                        "DocumentId": doc["DocumentId"],
                        "metadata": metadata,
                        "enriched_metadata_text": doc.get("enriched_metadata_text", ""),
                        "synthetic_content": "",
                        "full_text": doc.get("enriched_metadata_text", "")
                    }
                    documentos_enriquecidos.append(doc_enriquecido)
                    break

                print(f"⏳ Rate limit detectado. Esperando {wait_seconds:.1f}s antes de reintentar (intento {retry_count}/{max_retries})...")
                time.sleep(wait_seconds)
                backoff = min(backoff * 2, 300)

            except Exception as e:
                errores += 1
                print(f"\n❌ Error en documento {doc.get('DocumentId')}: {e}")
                doc_enriquecido = {
                    "DocumentId": doc["DocumentId"],
                    "metadata": metadata,
                    "enriched_metadata_text": doc.get("enriched_metadata_text", ""),
                    "synthetic_content": "",
                    "full_text": doc.get("enriched_metadata_text", "")
                }
                documentos_enriquecidos.append(doc_enriquecido)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(documentos_enriquecidos, f, ensure_ascii=False, indent=2)
                with open(checkpoint_path, 'w', encoding='utf-8') as cf:
                    json.dump({"last_index": idx + 1}, cf)
                break
    
    # Guardar resultado
    output_path = "data/mis_correos_con_contenido_sintetico.json"
    print(f"\n💾 Guardando resultado en {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(documentos_enriquecidos, f, ensure_ascii=False, indent=2)
    
    print(f"✅ ¡Completado!")
    print(f"\n📊 RESUMEN:")
    print(f"   - Documentos procesados: {len(documentos_enriquecidos)}")
    print(f"   - Documentos con errores: {errores}")
    print(f"   - Archivo generado: {output_path}")
    print(f"   - Tamaño aproximado: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
    
    # Mostrar ejemplo
    print(f"\n📄 EJEMPLO DE CONTENIDO GENERADO:")
    print("=" * 60)
    ejemplo = documentos_enriquecidos[0]
    print(f"Título: {ejemplo['metadata'].get('Title', 'N/A')}")
    print(f"Tipo: {ejemplo['metadata'].get('DocumentType', 'N/A')}")
    print(f"\nContenido generado (primeros 500 chars):")
    print(ejemplo['synthetic_content'][:500] + "...")
    print("=" * 60)
    
    print(f"\n💡 SIGUIENTE PASO:")
    print(f"   1. Revisar el archivo generado: {output_path}")
    print(f"   2. Si te gusta, re-ingestar con:")
    print(f"      python -m app.ingest --json_path {output_path} --project_id ACONEX")
    print(f"   3. Esto reemplazará los chunks actuales con contenido sintético realista")


if __name__ == "__main__":
    main()
