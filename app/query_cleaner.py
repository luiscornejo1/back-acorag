"""
Preprocesador de queries para búsqueda semántica mejorada
"""
import re
from typing import Set

# Palabras a eliminar (stopwords contextuales)
STOPWORDS: Set[str] = {
    # Palabras de solicitud
    'dame', 'busca', 'quiero', 'necesito', 'encuentra', 'muestra', 'ver',
    'mostrar', 'buscar', 'encontrar', 'traer', 'obtener', 'conseguir',
    
    # Conectores y preposiciones
    'sobre', 'acerca', 'relacionados', 'relacionadas', 'relacionado', 'relacionada',
    'con', 'de', 'del', 'la', 'el', 'los', 'las', 'un', 'una', 'unos', 'unas',
    'para', 'por', 'en', 'a', 'al', 'que', 'se', 'me', 'te',
    
    # Plurales genéricos
    'documentos', 'archivos', 'información', 'datos', 'cosas',
    
    # Palabras vagas
    'algo', 'algún', 'alguna', 'algunos', 'algunas', 'todo', 'todos', 'todas',
    'tipo', 'tipos', 'clase', 'clases'
}

def clean_query(query: str) -> str:
    """
    Limpia y optimiza una query para búsqueda semántica.
    
    Ejemplos:
        "dame documentos sobre seguridad" → "seguridad"
        "busca informes relacionados con costos" → "informes costos"
        "quiero ver planos estructurales" → "planos estructurales"
        "encuentrame algo de maria hoyos" → "maria hoyos"
    """
    # Convertir a minúsculas
    query_lower = query.lower().strip()
    
    # Remover signos de puntuación excepto espacios y guiones
    query_clean = re.sub(r'[^\w\s-]', ' ', query_lower)
    
    # Separar en palabras
    words = query_clean.split()
    
    # Filtrar stopwords
    important_words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    
    # Si se eliminaron todas las palabras, usar la query original
    if not important_words:
        return query.strip()
    
    # Unir palabras importantes
    cleaned = ' '.join(important_words)
    
    return cleaned


def should_clean_query(query: str) -> bool:
    """
    Determina si una query debería ser limpiada.
    No limpiar si parece ser una búsqueda específica directa.
    """
    query_lower = query.lower()
    
    # No limpiar si es una búsqueda muy corta y específica (1-2 palabras)
    words = query_lower.split()
    if len(words) <= 2:
        return False
    
    # Limpiar si contiene palabras de solicitud
    request_words = {'dame', 'busca', 'quiero', 'necesito', 'encuentra', 'muestra'}
    if any(word in query_lower for word in request_words):
        return True
    
    # Limpiar si contiene "documentos relacionados con"
    if 'documentos' in query_lower or 'relacionados' in query_lower:
        return True
    
    return False


# Tests
if __name__ == "__main__":
    test_queries = [
        "dame documentos relacionados con seguridad",
        "busca informes sobre costos del proyecto",
        "quiero ver planos estructurales",
        "encuentrame algo de maria hoyos",
        "necesito información acerca de cronogramas",
        "informe mensual costos",  # Ya específica, no debería limpiar mucho
        "planos estructurales",  # Ya específica
    ]
    
    print("=" * 70)
    print("TEST DE LIMPIEZA DE QUERIES")
    print("=" * 70)
    
    for query in test_queries:
        cleaned = clean_query(query)
        should_clean = should_clean_query(query)
        
        print(f"\n📝 Original: '{query}'")
        print(f"✨ Limpia:   '{cleaned}'")
        print(f"🎯 Limpiar:  {'SÍ' if should_clean else 'NO (ya es específica)'}")
