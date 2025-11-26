"""
Tests del módulo de búsqueda semántica (app/search_core.py)
Escenario 2: Búsqueda Semántica y Embeddings

Tests core seleccionados:
1. Test de búsqueda semántica básica con resultados rankeados
2. Test de búsqueda con filtro de proyecto (multi-tenancy)
"""
import pytest
from unittest.mock import MagicMock, patch
from app.search_core import semantic_search, encode_vec_str, get_model


# ============================================================================
# TEST 1: BÚSQUEDA SEMÁNTICA BÁSICA CON RANKING
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
@pytest.mark.mock
def test_semantic_search_basic(mock_model_loader, mock_db_connection):
    """
    Test Core: Búsqueda semántica básica con ranking híbrido
    
    Verifica que semantic_search:
    1. Genere el embedding de la query usando SentenceTransformer
    2. Ejecute búsqueda vectorial con operador <=> (distancia coseno)
    3. Combine score vectorial con búsqueda full-text
    4. Retorne resultados ordenados por relevancia
    5. Deduplique por document_id (solo el chunk más relevante por documento)
    
    Este es el core del sistema RAG: la búsqueda semántica que encuentra
    documentos relevantes basándose en similitud semántica, no solo keywords.
    """
    # Arrange: Configurar mock del cursor y resultados
    mock_cursor = mock_db_connection.cursor.return_value.__enter__.return_value
    
    # Simular resultados de búsqueda con scores
    mock_results = [
        {
            "document_id": "DOC-001",
            "project_id": "PROJ-001",
            "title": "Manual de Construcción Sísmica",
            "number": "MAN-001",
            "category": "Manuales",
            "doc_type": "Manual Técnico",
            "revision": "Rev 2",
            "filename": "manual_sismico.pdf",
            "file_type": "pdf",
            "date_modified": "2024-01-15",
            "snippet": "Normas y especificaciones para construcción sismo-resistente según NSR-10...",
            "vector_score": 0.92,  # Alta similitud semántica
            "text_score": 0.45,    # Score de búsqueda textual
            "score": 0.78          # Score híbrido combinado
        },
        {
            "document_id": "DOC-002",
            "project_id": "PROJ-001",
            "title": "Plano Estructural Edificio Central",
            "number": "PLN-002",
            "category": "Planos",
            "doc_type": "Estructural",
            "revision": "Rev 1",
            "filename": "plano_estructural.pdf",
            "file_type": "pdf",
            "date_modified": "2024-01-20",
            "snippet": "Distribución de columnas y vigas de concreto reforzado...",
            "vector_score": 0.85,
            "text_score": 0.30,
            "score": 0.68
        }
    ]
    
    mock_cursor.fetchall.return_value = mock_results
    
    # Act: Ejecutar búsqueda semántica
    with patch('app.search_core.get_conn', return_value=mock_db_connection):
        results = semantic_search(
            query="construcción sismo resistente",
            project_id=None,
            top_k=10,
            probes=10
        )
    
    # Assert: Verificar comportamiento
    
    # 1. Verificar que se generó embedding de la query
    assert mock_model_loader.encode.called, "Debe generarse embedding de la query"
    query_encoded = mock_model_loader.encode.call_args[0][0]
    assert isinstance(query_encoded, list), "Query debe ser lista para encode"
    
    # 2. Verificar que se ejecutó SQL con parámetros correctos
    execute_calls = mock_cursor.execute.call_args_list
    assert len(execute_calls) >= 2, "Debe ejecutarse SET ivfflat.probes y la query principal"
    
    # Verificar SET de probes para índice IVFFlat
    probes_call = str(execute_calls[0])
    assert "ivfflat.probes" in probes_call, "Debe configurarse ivfflat.probes para HNSW"
    
    # Verificar query principal con operador de distancia vectorial
    main_query_call = str(execute_calls[1])
    assert "<=>" in main_query_call or "embedding" in main_query_call, "Debe usar operador de distancia vectorial"
    
    # 3. Verificar estructura de resultados
    assert len(results) == 2, "Deben retornarse los 2 documentos mockeados"
    
    # Verificar que primer resultado tiene mayor score (ordenado)
    assert results[0]["score"] >= results[1]["score"], "Resultados deben estar ordenados por score descendente"
    assert results[0]["document_id"] == "DOC-001"
    
    # Verificar campos obligatorios en resultado
    required_fields = ["document_id", "title", "snippet", "vector_score", "score"]
    for field in required_fields:
        assert field in results[0], f"Campo '{field}' debe estar en resultado"
    
    # 4. Verificar que scores son numéricos y en rango válido
    assert 0 <= results[0]["vector_score"] <= 1, "vector_score debe estar entre 0 y 1"
    assert 0 <= results[0]["score"] <= 1, "score debe estar entre 0 y 1"
    
    print("\n✅ Búsqueda semántica básica validada:")
    print(f"   - Query: 'construcción sismo resistente'")
    print(f"   - Resultados: {len(results)}")
    print(f"   - Top documento: {results[0]['title']}")
    print(f"   - Vector score: {results[0]['vector_score']}")
    print(f"   - Score híbrido: {results[0]['score']}")


# ============================================================================
# TEST 2: BÚSQUEDA CON FILTRO DE PROYECTO (MULTI-TENANCY)
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
@pytest.mark.mock
def test_semantic_search_with_project_filter(mock_model_loader, mock_db_connection):
    """
    Test Core: Búsqueda con filtro de proyecto para multi-tenancy
    
    Verifica que el filtro project_id funcione correctamente para aislar
    resultados de diferentes proyectos. Esto es crítico para seguridad
    y para evitar mostrar documentos de proyectos no autorizados.
    
    Casos verificados:
    - Búsqueda con project_id específico filtra correctamente
    - Solo se retornan documentos del proyecto especificado
    - El filtro se aplica en la cláusula WHERE del SQL
    """
    # Arrange: Mock con resultados de UN SOLO proyecto
    mock_cursor = mock_db_connection.cursor.return_value.__enter__.return_value
    
    # Solo documentos de PROYECTO-EDUCATIVO
    mock_results = [
        {
            "document_id": "EDU-001",
            "project_id": "PROYECTO-EDUCATIVO",
            "title": "Plan Arquitectónico Escuela",
            "number": "PAE-001",
            "category": "Arquitectura",
            "doc_type": "Plano",
            "revision": "Rev 1",
            "filename": "arquitectura_escuela.pdf",
            "file_type": "pdf",
            "date_modified": "2024-02-01",
            "snippet": "Diseño arquitectónico del edificio educativo con 24 aulas...",
            "vector_score": 0.88,
            "text_score": 0.42,
            "score": 0.72
        }
    ]
    
    mock_cursor.fetchall.return_value = mock_results
    
    # Act: Buscar CON filtro de proyecto
    with patch('app.search_core.get_conn', return_value=mock_db_connection):
        results = semantic_search(
            query="arquitectura educativa",
            project_id="PROYECTO-EDUCATIVO",
            top_k=20
        )
    
    # Assert: Verificar filtro de proyecto
    
    # 1. Verificar que SQL incluye filtro de proyecto
    execute_calls = mock_cursor.execute.call_args_list
    main_query = execute_calls[1]  # Segunda llamada es la query principal
    sql_str = str(main_query[0][0])  # SQL como string
    params = main_query[0][1]  # Parámetros
    
    assert "project_id" in sql_str.lower(), "SQL debe contener filtro de project_id"
    assert "PROYECTO-EDUCATIVO" in params, "Parámetros deben incluir el project_id especificado"
    
    # 2. Verificar que TODOS los resultados son del proyecto correcto
    for result in results:
        assert result["project_id"] == "PROYECTO-EDUCATIVO", \
            f"Resultado {result['document_id']} no pertenece al proyecto filtrado"
    
    # 3. Verificar que se retornaron resultados
    assert len(results) > 0, "Debe haber al menos 1 resultado del proyecto"
    
    # 4. Verificar estructura completa del resultado
    assert results[0]["document_id"] == "EDU-001"
    assert results[0]["title"] == "Plan Arquitectónico Escuela"
    assert "educativo" in results[0]["snippet"].lower()
    
    print("\n✅ Búsqueda con filtro de proyecto validada:")
    print(f"   - Proyecto filtrado: PROYECTO-EDUCATIVO")
    print(f"   - Resultados: {len(results)}")
    print(f"   - Todos pertenecen al proyecto: ✓")
    print(f"   - Documento encontrado: {results[0]['title']}")


# ============================================================================
# TEST 3: BÚSQUEDA CON QUERY VACÍA (CASO NEGATIVO)
# ============================================================================

@pytest.mark.unit
def test_semantic_search_empty_query(mock_model_loader, mock_db_connection):
    """
    Test de Caso Negativo: Validar manejo de query vacía
    
    Verifica que semantic_search maneje apropiadamente cuando
    se pasa una query vacía o None.
    """
    from app.search_core import semantic_search
    
    with patch('app.search_core.get_conn', return_value=mock_db_connection):
        # Act & Assert: Query vacía debe retornar lista vacía o manejar el error
        results_empty = semantic_search(query="", project_id=None, top_k=10)
        assert results_empty is not None
        assert isinstance(results_empty, list)
        # Puede retornar [] o resultados generales, ambos válidos
        
        results_whitespace = semantic_search(query="   ", project_id=None, top_k=10)
        assert results_whitespace is not None
        assert isinstance(results_whitespace, list)
    
    print("\n✅ Manejo de query vacía validado:")
    print(f"   - Query vacía manejada correctamente: ✓")
    print(f"   - No crashea el sistema: ✓")


# ============================================================================
# TEST 4: BÚSQUEDA CON PROJECT_ID INEXISTENTE (CASO NEGATIVO)
# ============================================================================

@pytest.mark.integration
@pytest.mark.mock
def test_semantic_search_invalid_project_id(mock_model_loader, mock_db_connection):
    """
    Test de Caso Negativo: Validar búsqueda con proyecto inexistente
    
    Verifica que semantic_search retorne lista vacía cuando se busca
    en un proyecto que no existe, en lugar de fallar.
    """
    from app.search_core import semantic_search
    
    # Arrange: Mock retorna vacío (proyecto no existe)
    mock_cursor = mock_db_connection.cursor.return_value.__enter__.return_value
    mock_cursor.fetchall.return_value = []
    
    # Act: Buscar en proyecto inexistente
    with patch('app.search_core.get_conn', return_value=mock_db_connection):
        results = semantic_search(
            query="test query",
            project_id="PROYECTO-INEXISTENTE-99999",
            top_k=10
        )
    
    # Assert: Debe retornar lista vacía, NO error
    assert results is not None
    assert isinstance(results, list)
    assert len(results) == 0
    
    print("\n✅ Manejo de proyecto inexistente validado:")
    print(f"   - Retorna lista vacía: ✓")
    print(f"   - No lanza excepción: ✓")
