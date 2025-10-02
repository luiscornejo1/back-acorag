#!/usr/bin/env python3
"""
Prueba directa de búsqueda semántica sin servidor web
"""
import os
from dotenv import load_dotenv
from app.search_core import semantic_search

load_dotenv()

def test_direct_search():
    """
    Prueba búsquedas semánticas directamente en la base de datos
    """
    print("🔍 PRUEBA DIRECTA DE BÚSQUEDA SEMÁNTICA")
    print("=" * 50)
    
    # Consultas semánticas de prueba
    queries = [
        "planos de arquitectura",
        "documentos de construcción", 
        "especificaciones técnicas",
        "planos eléctricos",
        "distribución de espacios",
        "telecomunicaciones",
        "diseño estructural"
    ]
    
    for query in queries:
        print(f"\n🎯 Búsqueda: '{query}'")
        try:
            results = semantic_search(
                query=query,
                project_id=None,  # Sin filtro de proyecto
                top_k=3,
                probes=10
            )
            
            print(f"✅ Encontrados {len(results)} resultados:")
            
            for i, result in enumerate(results, 1):
                score = result.get('similarity_score', 'N/A')
                title = result.get('title', 'Sin título')[:80]
                doc_type = result.get('doc_type', 'N/A')
                category = result.get('category', 'N/A')
                
                print(f"   {i}. Score: {score:.3f}")
                print(f"      Título: {title}")
                print(f"      Tipo: {doc_type} | Categoría: {category}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("💡 Si ves resultados con scores > 0.5, ¡la búsqueda semántica funciona!")
    print("🧠 Notas:")
    print("   - Score > 0.7: Muy relevante")
    print("   - Score 0.5-0.7: Relevante")
    print("   - Score < 0.5: Poco relevante")

if __name__ == "__main__":
    test_direct_search()