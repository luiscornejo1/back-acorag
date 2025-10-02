#!/usr/bin/env python3
"""
Script para probar la búsqueda semántica
Demuestra que el sistema entiende CONCEPTOS, no solo palabras exactas
"""
import requests
import json
from typing import List, Dict

def test_semantic_search():
    """
    Prueba búsquedas semánticas vs sintácticas
    """
    base_url = "http://localhost:8000"
    
    print("🔍 PRUEBAS DE BÚSQUEDA SEMÁNTICA")
    print("=" * 50)
    
    # Consultas semánticas que deberían funcionar
    semantic_queries = [
        {
            "description": "Buscar problemas de cronograma",
            "query": "problemas con el cronograma del proyecto",
            "should_find": ["retraso", "demora", "cronograma", "tiempo", "entrega"]
        },
        {
            "description": "Buscar reuniones",
            "query": "necesito información sobre reuniones",
            "should_find": ["meeting", "junta", "cita", "encuentro"]
        },
        {
            "description": "Buscar información técnica",
            "query": "detalles técnicos de construcción",
            "should_find": ["especificaciones", "técnico", "ingeniería", "diseño"]
        },
        {
            "description": "Buscar presupuesto",
            "query": "información sobre costos y presupuesto",
            "should_find": ["dinero", "precio", "costo", "presupuesto", "financiero"]
        },
        {
            "description": "Buscar personal",
            "query": "información del equipo de trabajo",
            "should_find": ["empleados", "personal", "equipo", "trabajadores"]
        }
    ]
    
    for test_case in semantic_queries:
        print(f"\n🎯 {test_case['description']}")
        print(f"Query: '{test_case['query']}'")
        
        try:
            # Realizar búsqueda
            response = requests.post(f"{base_url}/search", json={
                "query": test_case["query"],
                "top_k": 3
            })
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Encontrados {len(results)} resultados")
                
                for i, result in enumerate(results, 1):
                    score = result.get('similarity_score', 'N/A')
                    title = result.get('title', 'Sin título')[:60]
                    content = result.get('content', result.get('chunk_text', ''))[:100]
                    
                    print(f"   {i}. Score: {score:.3f} | {title}")
                    print(f"      {content}...")
                    
                    # Verificar si encontró conceptos relacionados
                    content_lower = content.lower()
                    found_concepts = [word for word in test_case['should_find'] 
                                    if word.lower() in content_lower]
                    if found_concepts:
                        print(f"      🎯 Conceptos encontrados: {found_concepts}")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
    
    print("\n" + "=" * 50)
    print("💡 INTERPRETACIÓN DE RESULTADOS:")
    print("- Score > 0.7: Muy relevante (búsqueda semántica exitosa)")
    print("- Score 0.5-0.7: Relevante (conceptos relacionados)")
    print("- Score < 0.5: Poco relevante")
    print("\n🧠 La búsqueda semántica encuentra CONCEPTOS similares,")
    print("   no solo palabras exactas como búsqueda sintáctica.")

def test_multilingual_search():
    """
    Prueba búsquedas multiidioma
    """
    print("\n🌍 PRUEBAS MULTIIDIOMA")
    print("=" * 30)
    
    multilingual_tests = [
        {"spanish": "reunión del proyecto", "english": "project meeting"},
        {"spanish": "problema técnico", "english": "technical issue"},
        {"spanish": "cronograma de trabajo", "english": "work schedule"}
    ]
    
    base_url = "http://localhost:8000"
    
    for test in multilingual_tests:
        print(f"\n🔄 Comparando: '{test['spanish']}' vs '{test['english']}'")
        
        try:
            # Buscar en español
            resp_es = requests.post(f"{base_url}/search", json={
                "query": test["spanish"], "top_k": 3
            })
            
            # Buscar en inglés
            resp_en = requests.post(f"{base_url}/search", json={
                "query": test["english"], "top_k": 3
            })
            
            if resp_es.status_code == 200 and resp_en.status_code == 200:
                results_es = resp_es.json()
                results_en = resp_en.json()
                
                if results_es and results_en:
                    score_es = results_es[0].get('similarity_score', 0)
                    score_en = results_en[0].get('similarity_score', 0)
                    
                    print(f"   Español: {score_es:.3f}")
                    print(f"   English: {score_en:.3f}")
                    
                    if abs(score_es - score_en) < 0.1:
                        print("   ✅ Búsqueda multiidioma funcionando")
                    else:
                        print("   ⚠️ Diferencia significativa entre idiomas")
                else:
                    print("   ❌ Sin resultados en uno o ambos idiomas")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    # Verificar que el backend esté corriendo
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Backend conectado correctamente")
            test_semantic_search()
            test_multilingual_search()
        else:
            print("❌ Backend no responde correctamente")
    except Exception as e:
        print(f"❌ No se puede conectar al backend: {e}")
        print("🔧 Asegúrate de que el backend esté corriendo:")
        print("   cd backend-acorag")
        print("   .venv311\\Scripts\\activate")
        print("   uvicorn app.api:app --reload --port 8000")