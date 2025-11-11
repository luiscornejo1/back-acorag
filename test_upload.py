"""
Script de prueba para el endpoint de upload
Crea un documento de prueba y lo sube
"""
import requests
import json
import tempfile
import os

# URL del backend (cambia según tu entorno)
BASE_URL = "https://back-acorag-production.up.railway.app"  # Producción
# BASE_URL = "http://localhost:8000"  # Local

def test_upload_txt():
    """Test: Subir un archivo TXT simple"""
    print("=" * 60)
    print("TEST 1: Subir archivo TXT")
    print("=" * 60)
    
    # Crear archivo temporal
    content = """
INFORME TÉCNICO DE CONSTRUCCIÓN

Proyecto: Torre Empresarial Sky Plaza
Número de Documento: IT-2024-001
Fecha: 15 de Marzo 2024
Responsable: Ing. Juan Pérez

RESUMEN EJECUTIVO:
El presente informe detalla el avance de la obra correspondiente a la semana 
del 10 al 15 de marzo de 2024. Se alcanzó un 87% de avance en la estructura 
metálica del piso 12.

AVANCE DE OBRA:
- Excavación: 100% completado
- Cimentación: 100% completado
- Estructura hasta piso 11: 100% completado
- Estructura piso 12: 87% completado
- Instalaciones eléctricas: 65% completado
- Instalaciones sanitarias: 58% completado

MATERIALES UTILIZADOS:
- Concreto f'c=280 kg/cm²: 45 m³
- Acero de refuerzo: 8.5 toneladas
- Perfiles metálicos IPE 300: 120 metros lineales

PERSONAL:
- Ingenieros: 3
- Maestros de obra: 5
- Obreros: 28
- Operadores de maquinaria: 4

OBSERVACIONES:
Se presentó un retraso de 2 días debido a condiciones climáticas adversas 
(lluvia intensa) los días 13 y 14 de marzo.

PRÓXIMOS PASOS:
1. Completar estructura del piso 12 (fecha estimada: 20 marzo)
2. Iniciar estructura del piso 13 (fecha estimada: 22 marzo)
3. Avanzar instalaciones eléctricas pisos 8-11
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # Metadata del documento
        metadata = {
            "project": "Torre Sky Plaza",
            "type": "Informe Técnico",
            "category": "Construcción",
            "author": "Ing. Juan Pérez",
            "date": "2024-03-15"
        }
        
        # Subir archivo
        with open(temp_path, 'rb') as f:
            files = {'file': ('informe_tecnico.txt', f, 'text/plain')}
            data = {'metadata': json.dumps(metadata)}
            
            print(f"\n📤 Subiendo archivo a {BASE_URL}/upload...")
            response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ ÉXITO!")
            print(f"   Document ID: {result['data']['document_id']}")
            print(f"   Chunks creados: {result['data']['chunks_created']}")
            print(f"   Longitud de texto: {result['data']['text_length']}")
            print(f"\n📄 Metadata guardada:")
            print(json.dumps(result['data']['metadata'], indent=2, ensure_ascii=False))
            return result['data']['document_id']
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(response.text)
            return None
    
    finally:
        os.unlink(temp_path)

def test_upload_and_query(doc_id=None):
    """Test: Subir documento y hacer consulta inmediata"""
    print("\n" + "=" * 60)
    print("TEST 2: Subir archivo y consultar")
    print("=" * 60)
    
    content = """
CRONOGRAMA DE ACTIVIDADES - PROYECTO PUENTE LAS ÁGUILAS

Documento: CRON-2024-005
Fecha de Emisión: 10 de Abril 2024
Fase: Construcción

ACTIVIDADES PROGRAMADAS:

Semana 1 (15-21 Abril):
- Replanteo topográfico: 15-16 abril
- Excavación de zapatas: 17-21 abril
- Requisito: Aprobación de estudios de suelo

Semana 2 (22-28 Abril):
- Armado de acero en zapatas: 22-24 abril
- Vaciado de concreto zapatas: 25-26 abril
- Curado: 27-28 abril

Semana 3 (29 Abril - 5 Mayo):
- Encofrado de columnas: 29-30 abril
- Armado de acero columnas: 1-3 mayo
- Vaciado de columnas: 4-5 mayo

RECURSOS REQUERIDOS:
- Retroexcavadora: 5 días
- Mixer de concreto: 3 días
- Cuadrilla de fierreros: 12 días
- Operador de topógrafo: 2 días

HITOS CRÍTICOS:
✓ Entrega de estudios de suelo: 12 abril
✓ Aprobación municipal: 14 abril
⚠️ Vaciado de zapatas: 25-26 abril (crítico)
⚠️ Inspección de calidad: 28 abril

RESPONSABLES:
- Residente de Obra: Ing. María González
- Supervisor de Calidad: Ing. Carlos Ramírez
- Jefe de Topografía: Tec. Luis Fernández
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        metadata = {
            "project": "Puente Las Águilas",
            "type": "Cronograma",
            "category": "Planificación",
            "document_number": "CRON-2024-005",
            "date": "2024-04-10"
        }
        
        # Hacer consulta al subir
        question = "¿Cuándo está programado el vaciado de zapatas y quién es el responsable?"
        
        with open(temp_path, 'rb') as f:
            files = {'file': ('cronograma_puente.txt', f, 'text/plain')}
            data = {
                'metadata': json.dumps(metadata),
                'question': question
            }
            
            print(f"\n📤 Subiendo y consultando: '{question}'")
            response = requests.post(f"{BASE_URL}/upload-and-query", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ ÉXITO!")
            print(f"\n📄 Documento subido:")
            print(f"   ID: {result['upload_result']['document_id']}")
            print(f"   Chunks: {result['upload_result']['chunks_created']}")
            
            print(f"\n💬 RESPUESTA A LA CONSULTA:")
            print(f"   Pregunta: {result['query_result']['question']}")
            print(f"\n   Respuesta:")
            print(f"   {result['query_result']['answer']}")
            
            print(f"\n📚 Fuentes utilizadas: {len(result['query_result']['sources'])}")
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(response.text)
    
    finally:
        os.unlink(temp_path)

def test_search_uploaded():
    """Test: Buscar los documentos subidos anteriormente"""
    print("\n" + "=" * 60)
    print("TEST 3: Buscar documentos subidos")
    print("=" * 60)
    
    queries = [
        "avance de estructura piso 12",
        "cronograma vaciado zapatas",
        "Torre Sky Plaza materiales"
    ]
    
    for query in queries:
        print(f"\n🔍 Buscando: '{query}'")
        response = requests.post(
            f"{BASE_URL}/search",
            json={"query": query, "top_k": 3}
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"   ✅ Encontrados: {len(results)} resultados")
            for i, r in enumerate(results[:2], 1):
                print(f"   {i}. {r.get('title', 'Sin título')[:50]}... (score: {r.get('score', 0):.3f})")
        else:
            print(f"   ❌ ERROR: {response.status_code}")

if __name__ == "__main__":
    print("🚀 PRUEBA DE FUNCIONALIDAD DE UPLOAD\n")
    
    # Test 1: Upload simple
    doc_id = test_upload_txt()
    
    # Test 2: Upload + Query
    test_upload_and_query(doc_id)
    
    # Test 3: Búsqueda
    test_search_uploaded()
    
    print("\n" + "=" * 60)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 60)
